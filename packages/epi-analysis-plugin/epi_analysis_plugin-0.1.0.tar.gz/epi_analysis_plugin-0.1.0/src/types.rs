/// Optimized control data structure for efficient matching
#[derive(Debug)]
pub struct ControlRecord {
    pub pnr: String,
    pub birth_day: i32,
    pub mother_birth_day: Option<i32>,
    pub father_birth_day: Option<i32>,
}

/// Risk-set sampling record structure for time-to-event matching
#[derive(Debug, Clone)]
pub struct RiskSetRecord {
    pub pnr: String,
    pub birth_day: i32,
    pub mother_birth_day: Option<i32>,
    pub father_birth_day: Option<i32>,
    pub parity: Option<i64>,        // Birth order (PARITET)
    pub birth_type: Option<String>, // Birth type (singleton, doubleton, tripleton, quadleton, multiple)
    pub scd_status: String,
    pub scd_date: Option<i32>,          // Days since epoch for comparison
    pub death_date: Option<i32>,        // Days since epoch - child death
    pub emigration_date: Option<i32>,   // Days since epoch - child emigration
    pub mother_death_date: Option<i32>, // Days since epoch - mother death
    pub mother_emigration_date: Option<i32>, // Days since epoch - mother emigration
    pub father_death_date: Option<i32>, // Days since epoch - father death
    pub father_emigration_date: Option<i32>, // Days since epoch - father emigration
}
