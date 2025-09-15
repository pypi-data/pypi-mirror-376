use std::collections::HashMap;

use anyhow::Result;
use regex::Regex;

// Include the OPR_LAND categorization mapping at compile time
const OPR_LAND_MAPPING_RAW: &str = include_str!("../../../OPR_LAND.txt");

/// Ethnicity categories based on Danish SEPLINE guidelines
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EthnicityCategory {
    /// A1: Danish - Both individual and parents have Danish origin
    Danish,
    /// A2: Mixed Background - Individual has Danish origin, but one parent does not
    MixedBackground,
    /// B1: Western Immigrant - Individual from Western country, immigrant status
    WesternImmigrant,
    /// B2: Western Descendant - Individual from Western country, descendant status
    WesternDescendant,
    /// C1: Non-Western Immigrant - Individual from Non-Western country, immigrant status
    NonWesternImmigrant,
    /// C2: Non-Western Descendant - Individual from Non-Western country, descendant status
    NonWesternDescendant,
    /// Unknown - Missing or unclassifiable data
    Unknown,
}

impl EthnicityCategory {
    /// Convert ethnicity category to string for output
    pub const fn as_str(&self) -> &'static str {
        match self {
            Self::Danish => "danish",
            Self::MixedBackground => "mixed_background",
            Self::WesternImmigrant => "western_immigrant",
            Self::WesternDescendant => "western_descendant",
            Self::NonWesternImmigrant => "non_western_immigrant",
            Self::NonWesternDescendant => "non_western_descendant",
            Self::Unknown => "unknown",
        }
    }

    /// Get detailed description
    #[allow(dead_code)]
    pub const fn description(&self) -> &'static str {
        match self {
            Self::Danish => "Danish origin - individual and both parents born in Denmark",
            Self::MixedBackground => {
                "Mixed background - individual Danish origin, one parent non-Danish"
            },
            Self::WesternImmigrant => "Western immigrant - from Western country, immigrant status",
            Self::WesternDescendant => "Western descendant - from Western country, born in Denmark",
            Self::NonWesternImmigrant => {
                "Non-Western immigrant - from Non-Western country, immigrant status"
            },
            Self::NonWesternDescendant => {
                "Non-Western descendant - from Non-Western country, born in Denmark"
            },
            Self::Unknown => "Unknown or unclassifiable ethnicity",
        }
    }
}

/// OPR_LAND country origin categories
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OriginCategory {
    Danish,     // 0: Denmark, Greenland, Faroe Islands
    Western,    // 1: Western countries
    NonWestern, // 2: Non-Western countries
    Unknown,    // 9: Unknown/Missing
}

/// Immigration status from IE_TYPE
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ImmigrationStatus {
    Danish,     // 1: Danish (born in Denmark with Danish citizenship)
    Immigrant,  // 2: Immigrant (born abroad)
    Descendant, // 3: Descendant (born in Denmark, parents foreign)
    Unknown,    // Missing or other
}

/// Parse OPR_LAND mapping and create lookup table
pub fn create_opr_land_lookup() -> Result<HashMap<String, OriginCategory>> {
    let mut lookup = HashMap::new();
    let re = Regex::new(r"^(\d+): (.+)$")?;

    for line in OPR_LAND_MAPPING_RAW.lines() {
        if let Some(captures) = re.captures(line.trim()) {
            let code = captures.get(1).unwrap().as_str();
            let _description = captures.get(2).unwrap().as_str();

            // Map based on first digit or specific codes
            let category = match code {
                // Danish origin (0, 5100-5902)
                "0" => OriginCategory::Danish,
                code if code.starts_with("51") || code.starts_with("59") => OriginCategory::Danish,
                // Western countries (1, specific 5xxx codes)
                "1" => OriginCategory::Western,
                // Non-Western countries (2, specific 5xxx codes)
                "2" => OriginCategory::NonWestern,
                // Unknown (9, 5000, 5001, 5800, 5906)
                "9" | "5000" | "5001" | "5800" | "5906" => OriginCategory::Unknown,
                // Map 4-digit codes based on the category digit from the file
                code if code.len() >= 4 => {
                    // For 4-digit codes, we need to look at the category they belong to
                    // This is determined by their position in the file after category headers
                    continue; // We\'ll handle this in a second pass
                },
                _ => continue,
            };

            lookup.insert(code.to_string(), category);
        }
    }

    // Second pass: map 4-digit codes based on their section in the file
    let mut current_category = OriginCategory::Unknown;
    for line in OPR_LAND_MAPPING_RAW.lines() {
        if let Some(captures) = re.captures(line.trim()) {
            let code = captures.get(1).unwrap().as_str();

            // Update current category based on single-digit codes
            match code {
                "0" => current_category = OriginCategory::Danish,
                "1" => current_category = OriginCategory::Western,
                "2" => current_category = OriginCategory::NonWestern,
                "9" => current_category = OriginCategory::Unknown,
                // For 4-digit codes, use the current category
                code if code.len() >= 4 => {
                    lookup.insert(code.to_string(), current_category.clone());
                },
                _ => {},
            }
        }
    }

    println!("Loaded {} OPR_LAND code mappings", lookup.len());
    Ok(lookup)
}

/// Convert IE_TYPE to immigration status
pub const fn ie_type_to_status(ie_type: Option<i32>) -> ImmigrationStatus {
    match ie_type {
        Some(1) => ImmigrationStatus::Danish,
        Some(2) => ImmigrationStatus::Immigrant,
        Some(3) => ImmigrationStatus::Descendant,
        _ => ImmigrationStatus::Unknown,
    }
}
