use statrs::distribution::{ContinuousCDF, Normal};

use crate::types::AttGtResult;

/// Fill per-(g,t) statistics: t-stat, p-value, and CIs using provided z.
pub fn fill_attgt_stats(att_gt_results: &mut [AttGtResult], z: f64) {
    for r in att_gt_results {
        let se = r.se;
        if se > 1e-10 {
            r.t_stat = r.att / se;
            r.p_value = 2.0 * (1.0 - Normal::new(0.0, 1.0).unwrap().cdf(r.t_stat.abs()));
            r.conf_low = z.mul_add(-se, r.att);
            r.conf_high = z.mul_add(se, r.att);
        } else {
            r.t_stat = 0.0;
            r.p_value = 1.0;
            r.conf_low = r.att;
            r.conf_high = r.att;
        }
    }
}
