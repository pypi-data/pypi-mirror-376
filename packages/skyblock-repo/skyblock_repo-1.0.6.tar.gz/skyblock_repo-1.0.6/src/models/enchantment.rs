#[cfg(feature = "python")]
use pyo3::pyclass;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, PartialEq, Clone)]
#[serde(rename_all = "camelCase")]
#[cfg_attr(feature = "python", pyclass)]
pub struct SkyblockEnchantment {
	pub internal_id: String,
	pub name: Option<String>,
	pub category: Option<String>,
	pub source: Option<String>,
	pub min_level: Option<u8>,
	pub max_level: Option<u8>,
	#[serde(default)]
	pub items: Vec<String>,
}
