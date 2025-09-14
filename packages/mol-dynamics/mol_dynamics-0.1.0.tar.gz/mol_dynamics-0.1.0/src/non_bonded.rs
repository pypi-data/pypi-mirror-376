//! For VDW and Coulomb forces

#[cfg(feature = "cuda")]
use std::sync::Arc;
use std::{collections::HashMap, ops::AddAssign};

#[cfg(feature = "cuda")]
use cudarc::driver::{CudaModule, CudaStream};
use ewald::force_coulomb_short_range;
use lin_alg::{f32::Vec3, f64::Vec3 as Vec3F64};
use rayon::prelude::*;

#[cfg(feature = "cuda")]
use crate::forces::force_nonbonded_gpu;
use crate::{
    AtomDynamics, ComputationDevice, MdState,
    ambient::SimBox,
    forces::force_e_lj,
    water_opc::{ForcesOnWaterMol, O_EPS, O_SIGMA, WaterMol, WaterSite},
};

// Å. 9-12 should be fine; there is very little VDW force > this range due to
// the ^-7 falloff.
pub const CUTOFF_VDW: f32 = 12.0;
// const CUTOFF_VDW_SQ: f64 = CUTOFF_VDW * CUTOFF_VDW;

// Ewald SPME approximation for Coulomb force

// Instead of a hard cutoff between short and long-range forces, these
// parameters control a smooth taper.
// Our neighbor list must use the same cutoff as this, so we use it directly.

// We don't use a taper, for now.
// const LONG_RANGE_SWITCH_START: f64 = 8.0; // start switching (Å)
pub const LONG_RANGE_CUTOFF: f32 = 10.0;

// A bigger α means more damping, and a smaller real-space contribution. (Cheaper real), but larger
// reciprocal load.
// Common rule for α: erfc(α r_c) ≲ 10⁻⁴…10⁻⁵
pub const EWALD_ALPHA: f32 = 0.35; // Å^-1. 0.35 is good for cutoff = 10.
pub const PME_MESH_SPACING: f32 = 1.0;
// SPME order‑4 B‑spline interpolation
pub const SPME_N: usize = 64;

// See Amber RM, section 15, "1-4 Non-Bonded Interaction Scaling"
// "Non-bonded interactions between atoms separated by three consecutive bonds... require a special
// treatment in Amber force fields."
// "By default, vdW 1-4 interactions are divided (scaled down) by a factor of 2.0, electrostatic 1-4 terms by a factor
// of 1.2."
const SCALE_LJ_14: f32 = 0.5;
pub const SCALE_COUL_14: f32 = 1.0 / 1.2;

// Multiply by this to convert partial charges from elementary charge (What we store in Atoms loaded from mol2
// files and amino19.lib.) to the self-consistent amber units required to calculate Coulomb force.
// We apply this to dynamic and static atoms when building Indexed params, and to water molecules
// on their construction.
pub const CHARGE_UNIT_SCALER: f32 = 18.2223;

// (indices), (sigma, eps)
// pub type LjTable = HashMap<(usize, usize), (f32, f32)>;

/// We use this to load the correct data from LJ lookup tables. Since we use indices,
/// we must index correctly into the dynamic, or static tables. We have single-index lookups
/// for atoms acting on water, since there is only one O LJ type.
#[derive(Debug)]
pub enum LjTableIndices {
    /// (tgt, src)
    DynDyn((usize, usize)),
    /// (dyn tgt or src))
    DynWater(usize),
    /// One value, stored as a constant (Water O -> Water O)
    WaterWater,
}

/// We cache sigma and eps on the first step, then use it on the others. This increases
/// memory use, and reduces CPU use. We use indices, as they're faster than HashMaps.
#[derive(Default)]
pub struct LjTables {
    /// Keys: (Dynamic, Dynamic). For acting on dynamic atoms.
    pub dynamic: Vec<(f32, f32)>,
    /// Keys: Dynamic. Water acting on water O.
    /// Water tables are simpler than ones on dynamic: no combinations needed, as the source is a single
    /// target atom type: O (water).
    pub water_dyn: Vec<(f32, f32)>,
    pub n_dyn: usize,
}

// todo note: On large systems, this can have very high memory use. Consider
// todo setting up your table by atom type, instead of by atom, if that proves to be a problem.
impl LjTables {
    /// Create an indexed table, flattened.
    pub fn new(atoms: &[AtomDynamics], water: &[WaterMol]) -> Self {
        let n_dyn = atoms.len();

        let mut dynamic = Vec::with_capacity(n_dyn.saturating_sub(1) * n_dyn);

        for (i, atom_0) in atoms.iter().enumerate() {
            for (j, atom_1) in atoms.iter().enumerate() {
                if i == j {
                    continue;
                }
                let (σ, ε) = combine_lj_params(atom_0, atom_1);
                dynamic.push((σ, ε));
            }
        }

        // One LJ pair per dynamic atom vs water O:
        let mut water_dyn = Vec::with_capacity(n_dyn);
        for atom in atoms {
            let σ = 0.5 * (atom.lj_sigma + O_SIGMA);
            let ε = (atom.lj_eps * O_EPS).sqrt();
            water_dyn.push((σ, ε));
        }

        Self {
            dynamic,
            water_dyn,
            n_dyn,
        }
    }

    /// Get (σ, ε)
    pub fn lookup(&self, i: &LjTableIndices) -> (f32, f32) {
        match i {
            LjTableIndices::DynDyn((i0, i1)) => {
                // Row-major over N×N with diagonal removed.
                let row_stride = self.n_dyn - 1;
                let col = if *i1 < *i0 { *i1 } else { *i1 - 1 }; // Skip the diagonal
                let index = i0 * row_stride + col;

                self.dynamic[index]
            }
            LjTableIndices::DynWater(ix) => self.water_dyn[*ix],
            LjTableIndices::WaterWater => (O_SIGMA, O_EPS),
        }
    }
}

impl AddAssign<Self> for ForcesOnWaterMol {
    fn add_assign(&mut self, rhs: Self) {
        self.f_o += rhs.f_o;
        self.f_h0 += rhs.f_h0;
        self.f_h1 += rhs.f_h1;
        self.f_m += rhs.f_m;
    }
}

#[derive(Copy, Clone)]
enum BodyRef {
    Dyn(usize),
    // Static(usize),
    Water { mol: usize, site: WaterSite },
}

impl BodyRef {
    fn get<'a>(&self, dyns: &'a [AtomDynamics], waters: &'a [WaterMol]) -> &'a AtomDynamics {
        match *self {
            BodyRef::Dyn(i) => &dyns[i],
            BodyRef::Water { mol, site } => match site {
                WaterSite::O => &waters[mol].o,
                WaterSite::M => &waters[mol].m,
                WaterSite::H0 => &waters[mol].h0,
                WaterSite::H1 => &waters[mol].h1,
            },
        }
    }
}

struct NonBondedPair {
    tgt: BodyRef,
    src: BodyRef,
    scale_14: bool,
    lj_indices: LjTableIndices,
    calc_lj: bool,
    calc_coulomb: bool,
    symmetric: bool,
}

/// Add a force into the right accumulator (dyn or water). Static never accumulates.
fn add_to_sink(
    sink_dyn: &mut [Vec3F64],
    sink_wat: &mut [ForcesOnWaterMol],
    body_type: BodyRef,
    f: Vec3F64,
) {
    match body_type {
        BodyRef::Dyn(i) => sink_dyn[i] += f,
        BodyRef::Water { mol, site } => match site {
            WaterSite::O => sink_wat[mol].f_o += f,
            WaterSite::M => sink_wat[mol].f_m += f,
            WaterSite::H0 => sink_wat[mol].f_h0 += f,
            WaterSite::H1 => sink_wat[mol].f_h1 += f,
        },
        // BodyRef::Static(_) => (),
    }
}

/// Applies non-bonded force in parallel (thread-pool) over a set of atoms, with indices assigned
/// upstream.
///
/// Return the virial pair component we accumulate. For use with the temp/barostat. (kcal/mol)
fn calc_force(
    pairs: &[NonBondedPair],
    atoms_dyn: &[AtomDynamics],
    water: &[WaterMol],
    cell: &SimBox,
    lj_tables: &LjTables,
) -> (Vec<Vec3F64>, Vec<ForcesOnWaterMol>, f64, f64) {
    let n_dyn = atoms_dyn.len();
    let n_wat = water.len();

    pairs
        .par_iter()
        .fold(
            || {
                (
                    // Sums as f64.
                    vec![Vec3F64::new_zero(); n_dyn],
                    vec![ForcesOnWaterMol::default(); n_wat],
                    0.0_f64, // Virial sum
                    0.0_f64, // Energy sum
                )
            },
            |(mut acc_d, mut acc_w, mut virial, mut energy), p| {
                let a_t = p.tgt.get(atoms_dyn, water);
                let a_s = p.src.get(atoms_dyn, water);

                let (f, e_pair) = f_nonbonded(
                    &mut virial,
                    a_t,
                    a_s,
                    cell,
                    p.scale_14,
                    &p.lj_indices,
                    lj_tables,
                    p.calc_lj,
                    p.calc_coulomb,
                );

                // Convert to f64 prior to summing.
                let f: Vec3F64 = f.into();
                add_to_sink(&mut acc_d, &mut acc_w, p.tgt, f);
                if p.symmetric {
                    add_to_sink(&mut acc_d, &mut acc_w, p.src, -f);
                }

                // We are not interested, in this point, at energy that does not involve our dyanamic (ligand) atoms.
                // We skip water-water, and water-static interations.
                let involves_dyn =
                    matches!(p.tgt, BodyRef::Dyn(_)) || matches!(p.src, BodyRef::Dyn(_));

                if involves_dyn {
                    energy += e_pair as f64;
                }

                (acc_d, acc_w, virial, energy)
            },
        )
        .reduce(
            || {
                (
                    vec![Vec3F64::new_zero(); n_dyn],
                    vec![ForcesOnWaterMol::default(); n_wat],
                    0.0_f64,
                    0.0_f64,
                )
            },
            |(mut f_on_dyn, mut f_on_water, virial_a, e_a), (db, wb, virial_b, e_b)| {
                for i in 0..n_dyn {
                    f_on_dyn[i] += db[i];
                }
                for i in 0..n_wat {
                    f_on_water[i].f_o += wb[i].f_o;
                    f_on_water[i].f_m += wb[i].f_m;
                    f_on_water[i].f_h0 += wb[i].f_h0;
                    f_on_water[i].f_h1 += wb[i].f_h1;
                }

                (f_on_dyn, f_on_water, virial_a + virial_b, e_a + e_b)
            },
        )
}

/// Instead of thread pools, uses the GPU.
#[cfg(feature = "cuda")]
fn calc_force_cuda(
    stream: &Arc<CudaStream>,
    module: &Arc<CudaModule>,
    pairs: &[NonBondedPair],
    atoms_dyn: &[AtomDynamics],
    water: &[WaterMol],
    cell: &SimBox,
    lj_tables: &LjTables,
    cutoff_ewald: f32,
    alpha_ewald: f32,
) -> (Vec<Vec3F64>, Vec<ForcesOnWaterMol>, f64, f64) {
    let n_dyn = atoms_dyn.len();
    let n_water = water.len();

    let n = pairs.len();

    let mut posits_tgt: Vec<Vec3> = Vec::with_capacity(n);
    let mut posits_src: Vec<Vec3> = Vec::with_capacity(n);

    let mut sigmas = Vec::with_capacity(n);
    let mut epss = Vec::with_capacity(n);

    let mut qs_tgt = Vec::with_capacity(n);
    let mut qs_src = Vec::with_capacity(n);

    let mut scale_14s = Vec::with_capacity(n);

    let mut tgt_is: Vec<u32> = Vec::with_capacity(n);
    let mut src_is: Vec<u32> = Vec::with_capacity(n);

    let mut calc_ljs = Vec::with_capacity(n);
    let mut calc_coulombs = Vec::with_capacity(n);
    let mut symmetric = Vec::with_capacity(n);

    // Unpack BodyRef to fields. It doesn't map neatly to CUDA flattening primitives.

    // These atom and water types are so the Kernel can assign to the correct output arrays.
    // 0 means Dyn, 1 means Water.
    let mut atom_types_tgt = vec![0; n];
    // 0 for not-water or N/A. 1 = O, 2 = M, 3 = H0, 4 = H1.
    // Pre-allocated to 0, which we use for dyn atom targets.
    let mut water_types_tgt = vec![0; n];

    let mut atom_types_src = vec![0; n];
    let mut water_types_src = vec![0; n];

    for (i, pair) in pairs.iter().enumerate() {
        let atom_tgt = match pair.tgt {
            BodyRef::Dyn(j) => {
                tgt_is.push(j as u32);
                &atoms_dyn[j]
            }
            BodyRef::Water { mol: j, site } => {
                tgt_is.push(j as u32);

                // Mark so the kernel will use the water output.
                atom_types_tgt[i] = 1;
                water_types_tgt[i] = site as u8;

                match site {
                    WaterSite::O => &water[j].o,
                    WaterSite::M => &water[j].m,
                    WaterSite::H0 => &water[j].h0,
                    WaterSite::H1 => &water[j].h1,
                }
            }
            _ => unreachable!(),
        };

        let atom_src = match pair.src {
            BodyRef::Dyn(j) => {
                src_is.push(j as u32);
                &atoms_dyn[j]
            }
            BodyRef::Water { mol: j, site } => {
                src_is.push(j as u32);

                // Mark so the kernel will use the water output. (In case of dyn/water symmetric)
                atom_types_src[i] = 1;
                water_types_src[i] = site as u8;
                match site {
                    WaterSite::O => &water[j].o,
                    WaterSite::M => &water[j].m,
                    WaterSite::H0 => &water[j].h0,
                    WaterSite::H1 => &water[j].h1,
                }
            }
        };

        posits_tgt.push(atom_tgt.posit);
        posits_src.push(atom_src.posit);

        let (σ, ε) = lj_tables.lookup(&pair.lj_indices);

        sigmas.push(σ);
        epss.push(ε);

        qs_tgt.push(atom_tgt.partial_charge);
        qs_src.push(atom_src.partial_charge);

        scale_14s.push(pair.scale_14);

        calc_ljs.push(pair.calc_lj);
        calc_coulombs.push(pair.calc_coulomb);
        symmetric.push(pair.symmetric);
    }

    // 1-4 scaling, and the symmetric case handled in the kernel.

    let cell_extent: Vec3 = cell.extent.into();

    // Note that we perform virial accumulation as f64, even on GPU.
    let (f_on_dyn, f_on_water, virial, energy) = force_nonbonded_gpu(
        stream,
        module,
        &tgt_is,
        &src_is,
        &posits_tgt,
        &posits_src,
        &sigmas,
        &epss,
        &qs_tgt,
        &qs_src,
        &atom_types_tgt,
        &water_types_tgt,
        &atom_types_src,
        &water_types_src,
        &scale_14s,
        &calc_ljs,
        &calc_coulombs,
        &symmetric,
        cutoff_ewald as f32,
        alpha_ewald as f32,
        cell_extent,
        n_dyn,
        n_water,
    );

    let f_on_dyn = f_on_dyn.into_iter().map(|f| f.into()).collect();

    (f_on_dyn, f_on_water, virial, energy)
}

impl MdState {
    /// Run the appropriate force-computation function to get force on dynamic atoms, force
    /// on water atoms, and virial sum for the barostat. Uses GPU if available.
    fn apply_force(&mut self, dev: &ComputationDevice, pairs: &[NonBondedPair]) {
        let (f_on_dyn, f_on_water, virial, energy) = match dev {
            ComputationDevice::Cpu => calc_force(
                &pairs,
                &self.atoms,
                &self.water,
                &self.cell,
                &self.lj_tables,
            ),
            #[cfg(feature = "cuda")]
            ComputationDevice::Gpu((stream, module)) => calc_force_cuda(
                stream,
                module,
                &pairs,
                &self.atoms,
                &self.water,
                &self.cell,
                &self.lj_tables,
                LONG_RANGE_CUTOFF,
                EWALD_ALPHA,
            ),
        };

        // `.into()` below converts accumulated forces to f32.
        for (i, tgt) in self.atoms.iter_mut().enumerate() {
            let f: Vec3 = f_on_dyn[i].into();
            tgt.accel += f;
        }

        for (i, tgt) in self.water.iter_mut().enumerate() {
            let f = f_on_water[i];
            let f_0: Vec3 = f.f_o.into();
            let f_m: Vec3 = f.f_m.into();
            let f_h0: Vec3 = f.f_h0.into();
            let f_h1: Vec3 = f.f_h1.into();

            tgt.o.accel += f_0;
            tgt.m.accel += f_m;
            tgt.h0.accel += f_h0;
            tgt.h1.accel += f_h1;
        }

        self.barostat.virial_pair_kcal += virial;
        self.potential_energy += energy;
    }

    /// Applies Coulomb and Van der Waals (Lennard-Jones) forces on dynamic atoms, in place.
    /// We use the MD-standard [S]PME approach to handle approximated Coulomb forces. This function
    /// applies forces from dynamic, static, and water sources.
    pub fn apply_nonbonded_forces(&mut self, dev: &ComputationDevice) {
        let n_dyn = self.atoms.len();
        let n_water_mols = self.water.len();

        let sites = [WaterSite::O, WaterSite::M, WaterSite::H0, WaterSite::H1];

        // todo: You can probably consolidate even further. Instead of calling apply_force
        // todo per each category, you can assemble one big set of pairs, and call it once.
        // todo: This has performance and probably code organization benefits. Maybe try
        // todo after you get the intial version working. Will have to add symmetric to pairs.

        // ------ Forces from other dynamic atoms on dynamic ones ------

        // Exclusions and scaling apply to dynamic-dynamic interactions only.
        let exclusions = &self.pairs_excluded_12_13;
        let scaled_set = &self.pairs_14_scaled;

        // Set up pairs ahead of time; conducive to parallel iteration. We skip excluded pairs,
        // and mark scaled ones. These pairs, in symmetric cases (e.g. dynamic-dynamic), only
        let pairs_dyn_dyn: Vec<_> = (0..n_dyn)
            .flat_map(|i_tgt| {
                self.neighbors_nb.dy_dy[i_tgt]
                    .iter()
                    .copied()
                    .filter(move |&j| j > i_tgt) // Ensure stable order
                    .filter_map(move |i_src| {
                        let key = (i_tgt, i_src);
                        if exclusions.contains(&key) {
                            return None;
                        }
                        let scale_14 = scaled_set.contains(&key);

                        Some(NonBondedPair {
                            tgt: BodyRef::Dyn(i_tgt),
                            src: BodyRef::Dyn(i_src),
                            scale_14,
                            lj_indices: LjTableIndices::DynDyn(key),
                            calc_lj: true,
                            calc_coulomb: true,
                            symmetric: true,
                        })
                    })
            })
            .collect();

        // Forces from water on dynamic atoms, and vice-versa
        let mut pairs_dyn_water: Vec<_> = (0..n_dyn)
            .flat_map(|i_dyn| {
                self.neighbors_nb.dy_water[i_dyn]
                    .iter()
                    .copied()
                    .flat_map(move |i_water| {
                        sites.into_iter().map(move |site| NonBondedPair {
                            tgt: BodyRef::Dyn(i_dyn),
                            src: BodyRef::Water { mol: i_water, site },
                            scale_14: false,
                            // todo: Ensure you reverse it.
                            lj_indices: LjTableIndices::DynWater(i_dyn),
                            calc_lj: site == WaterSite::O,
                            calc_coulomb: site != WaterSite::O,
                            symmetric: true,
                        })
                    })
            })
            .collect();

        // ------ Water on water ------
        let mut pairs_water_water = Vec::new();

        for i_0 in 0..n_water_mols {
            for &i_1 in &self.neighbors_nb.water_water[i_0] {
                if i_1 <= i_0 {
                    continue;
                } // unique (i0,i1)

                for &site_0 in &sites {
                    for &site_1 in &sites {
                        let calc_lj = site_0 == WaterSite::O && site_1 == WaterSite::O;
                        let calc_coulomb = site_0 != WaterSite::O && site_1 != WaterSite::O;

                        if !(calc_lj || calc_coulomb) {
                            continue;
                        }

                        pairs_water_water.push(NonBondedPair {
                            tgt: BodyRef::Water {
                                mol: i_0,
                                site: site_0,
                            },
                            src: BodyRef::Water {
                                mol: i_1,
                                site: site_1,
                            },
                            scale_14: false,
                            lj_indices: LjTableIndices::WaterWater,
                            calc_lj,
                            calc_coulomb,
                            symmetric: true,
                        });
                    }
                }
            }
        }

        // todo: Consider just removing the functional parts above, and add to `pairs` directly.
        // Combine pairs into a single set; we compute in one parallel pass.
        let len_added = pairs_dyn_water.len() + pairs_water_water.len();

        let mut pairs = pairs_dyn_dyn;
        pairs.reserve(len_added);

        pairs.append(&mut pairs_dyn_water);
        pairs.append(&mut pairs_water_water);

        self.apply_force(dev, &pairs);
    }
}

/// Lennard Jones and (short-range) Coulomb forces. Used by water and non-water.
/// We run long-range SPME Coulomb force separately.
///
/// We use a hard distance cutoff for Vdw, enabled by its ^-7 falloff.
/// Returns energy as well.
pub fn f_nonbonded(
    virial_w: &mut f64,
    tgt: &AtomDynamics,
    src: &AtomDynamics,
    cell: &SimBox,
    scale14: bool, // See notes earlier in this module.
    lj_indices: &LjTableIndices,
    lj_tables: &LjTables,
    // These flags are for use with forces on water.
    calc_lj: bool,
    calc_coulomb: bool,
) -> (Vec3, f32) {
    let diff = cell.min_image(tgt.posit - src.posit);

    // We compute these dist-related values once, and share them between
    // LJ and Coulomb.
    let dist_sq = diff.magnitude_squared();

    if dist_sq < 1e-12 {
        return (Vec3::new_zero(), 0.);
    }

    let dist = dist_sq.sqrt();
    let inv_dist = 1.0 / dist;
    let dir = diff * inv_dist;

    let (f_lj, energy_lj) = if !calc_lj || dist > CUTOFF_VDW {
        (Vec3::new_zero(), 0.)
    } else {
        let (σ, ε) = lj_tables.lookup(lj_indices);

        let (mut f, mut e) = force_e_lj(dir, inv_dist, σ, ε);
        if scale14 {
            f *= SCALE_LJ_14;
            e *= SCALE_LJ_14;
        }
        (f, e)
    };

    // We assume that in the AtomDynamics structs, charges are already scaled to Amber units.
    // (No longer in elementary charge)
    let (mut f_coulomb, mut energy_coulomb) = if !calc_coulomb {
        (Vec3::new_zero(), 0.)
    } else {
        force_coulomb_short_range(
            dir,
            dist,
            inv_dist,
            tgt.partial_charge,
            src.partial_charge,
            // (LONG_RANGE_SWITCH_START, LONG_RANGE_CUTOFF),
            LONG_RANGE_CUTOFF,
            EWALD_ALPHA,
        )

        // force_coulomb(dir, dist, tgt.partial_charge, src.partial_charge, 1e-6)
    };

    // // todo: Temp dir test
    // if dist < 3.1 && dist > 2.9 {
    //     println!("Dist: {:.2}, Src: {:.2} Tgt: {:.2}, q0: {:.2} q1: {:.2} LJ: {:.5} Coul: {:.5}", dist, src.posit.x, tgt.posit.x, src.partial_charge, tgt.partial_charge, f_lj.x, f_coulomb.x);
    // }

    // See Amber RM, section 15, "1-4 Non-Bonded Interaction Scaling"
    if scale14 {
        f_coulomb *= SCALE_COUL_14;
        energy_coulomb *= SCALE_COUL_14;
    }

    // todo: How do we prevent accumulating energy on static atoms and water?

    let force = f_lj + f_coulomb;
    let energy = energy_lj + energy_coulomb;

    *virial_w += diff.dot(force) as f64;

    (force, energy)
}

/// Helper. Returns σ, ε between an atom pair. Atom order passed as params doesn't matter.
/// Note that this uses the traditional algorithm; not the Amber-specific version: We pre-set
/// atom-specific σ and ε to traditional versions on ingest, and when building water.
fn combine_lj_params(atom_0: &AtomDynamics, atom_1: &AtomDynamics) -> (f32, f32) {
    let σ = 0.5 * (atom_0.lj_sigma + atom_1.lj_sigma);
    let ε = (atom_0.lj_eps * atom_1.lj_eps).sqrt();

    (σ, ε)
}
