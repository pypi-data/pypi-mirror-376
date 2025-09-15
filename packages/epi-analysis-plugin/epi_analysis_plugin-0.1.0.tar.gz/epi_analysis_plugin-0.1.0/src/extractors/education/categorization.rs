use std::collections::HashMap;

use anyhow::{anyhow, Result};
use regex::Regex;

use super::EducationRecord;

// Include the HFAUDD categorization mapping at compile time
const HFAUDD_CATEGORIZATION_RAW: &str = include_str!("../../../hfaudd_categorization.txt");

/// Education level categories based on HFAUDD.md
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EducationLevel {
    Short,   // 10, 15
    Medium,  // 20, 30, 35
    Long,    // 40, 50, 60, 70, 80
    Unknown, // 90, missing
}

impl EducationLevel {
    /// Convert education level to string for output
    pub const fn as_str(&self) -> &'static str {
        match self {
            Self::Short => "short",
            Self::Medium => "medium",
            Self::Long => "long",
            Self::Unknown => "unknown",
        }
    }

    /// Get numeric priority for ranking (higher = more education)
    pub const fn priority(&self) -> u8 {
        match self {
            Self::Unknown => 0,
            Self::Short => 1,
            Self::Medium => 2,
            Self::Long => 3,
        }
    }
}

/// Parse HFAUDD categorization mapping and create lookup table
pub fn create_hfaudd_lookup() -> Result<HashMap<String, u8>> {
    let mut lookup = HashMap::new();
    let re = Regex::new(r"^(\d+)=\'(\d{2})\s+")?;

    for line in HFAUDD_CATEGORIZATION_RAW.lines() {
        if let Some(captures) = re.captures(line) {
            let hfaudd_code = captures.get(1).unwrap().as_str().to_string();
            let level_str = captures.get(2).unwrap().as_str();

            if let Ok(level_code) = level_str.parse::<u8>() {
                lookup.insert(hfaudd_code, level_code);
            }
        }
    }

    if lookup.is_empty() {
        return Err(anyhow!("Failed to parse any HFAUDD categorizations"));
    }

    println!("Loaded {} HFAUDD categorizations", lookup.len());
    Ok(lookup)
}

/// Convert HFAUDD code to education category
/// First checks for specific middle school codes, then falls back to level code categorization
pub fn hfaudd_to_category(hfaudd_code: &str, level_code: Option<u8>) -> EducationLevel {
    // Special handling for middle school codes (realskolen)
    match hfaudd_code {
        "1021" | "1022" | "1023" | "1121" | "1122" | "1123" | "1423" | "1522" | "1523" | "1721"
        | "1722" | "1723" => EducationLevel::Medium,
        _ => {
            // Fall back to level code categorization
            match level_code {
                Some(10) | Some(15) => EducationLevel::Short,
                Some(20) | Some(30) | Some(35) => EducationLevel::Medium,
                Some(40) | Some(50) | Some(60) | Some(70) | Some(80) => EducationLevel::Long,
                Some(90) | _ => EducationLevel::Unknown,
            }
        },
    }
}

/// Check if education record is temporally valid at index date
pub fn is_temporally_valid(record: &EducationRecord, index_date: i32) -> bool {
    let valid_from_ok = record.valid_from.is_none_or(|vfra| vfra <= index_date);
    let valid_to_ok = record.valid_to.is_none_or(|vtil| index_date <= vtil);

    valid_from_ok && valid_to_ok
}
