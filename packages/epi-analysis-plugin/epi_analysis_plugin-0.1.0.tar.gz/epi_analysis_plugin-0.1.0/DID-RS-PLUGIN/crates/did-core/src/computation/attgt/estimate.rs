use faer::Mat;

#[derive(Debug)]
pub struct AttGtEstimate {
    pub att: f64,
    pub inf: Mat<f64>,
    pub n1: usize,
}
