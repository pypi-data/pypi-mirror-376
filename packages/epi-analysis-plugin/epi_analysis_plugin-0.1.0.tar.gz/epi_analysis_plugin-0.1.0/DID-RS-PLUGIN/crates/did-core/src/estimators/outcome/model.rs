use faer::Mat;

pub trait OutcomeModel {
    fn fit(&self, x: &Mat<f64>, y: &Mat<f64>, w: Option<&[f64]>) -> Mat<f64>;
    fn predict(&self, x: &Mat<f64>, beta: &Mat<f64>) -> Vec<f64>;
}
