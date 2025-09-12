use std::{collections::HashMap, fs::File, path::Path, sync::Arc};

use anyhow::{bail, Context, Ok, Result};
use openmander_map::{GeoId, GeoType, Map};
use openmander_partition::{Partition};
use polars::{frame::DataFrame, io::{SerReader, SerWriter}, prelude::{CsvReader, CsvWriter, DataType, NamedFrom}, series::Series};

/// A districting plan, assigning blocks to districts.
#[derive(Debug)]
pub struct Plan {
    pub(crate) map: Arc<Map>,
    pub(crate) num_districts: u32, // number of districts (excluding unassigned 0)
    pub(crate) partition: Partition,
}

impl Plan {
    /// Create a new empty plan with a set number of districts.
    pub fn new(map: impl Into<Arc<Map>>, num_districts: u32) -> Self {
        let map: Arc<Map> = map.into();
        let partition = Partition::new(
            num_districts as usize + 1,
            map.get_layer(GeoType::Block).graph_handle()
        );

        Self { map, num_districts, partition }
    }

    /// Get the number of districts in this plan (excluding unassigned 0).
    #[inline] pub fn num_districts(&self) -> u32 { self.num_districts }

    /// Get the list of weight series available in the map's node weights.
    #[inline]
    pub fn get_series(&self) -> Vec<&str> {
        self.partition.graph().node_weights().series()
    }

    /// Set the block assignments for the plan.
    pub fn set_assignments(&mut self, assignments: HashMap<GeoId, u32>) -> Result<()> {
        // map the list of geo_ids to their value in assignments, using 0 if not found
        self.partition.set_assignments(
            self.map.get_layer(GeoType::Block).geo_ids().iter()
                .map(|geo_id| assignments.get(geo_id).copied().unwrap_or(0))
                .collect()
        );

        Ok(())
    }

    /// Get the block assignments for the plan.
    pub fn get_assignments(&self) -> Result<HashMap<GeoId, u32>> {
        let assignments = self.map.get_layer(GeoType::Block).index().clone().into_iter()
            .map(|(geo_id, i)| (geo_id, self.partition.assignment(i as usize)))
            .collect();

        Ok(assignments)
    }

    /// Load a plan from a CSV block assignment file.
    pub fn load_csv(&mut self, csv_path: &Path) -> Result<()> {
        // Read the CSV file into a Polars DataFrame, throwing an error if the file isn't found
        let df = CsvReader::new(File::open(csv_path)
            .with_context(|| format!("[Plan.from_csv] Failed to open CSV file: {}", csv_path.display()))?)
            .finish()
            .with_context(|| format!("[Plan.from_csv] Failed to read CSV file: {}", csv_path.display()))?;

        let block_layer = self.map.get_layer(GeoType::Block);

        // assert CSV has at least two columns
        if df.width() < 2 { bail!("[Plan.from_csv] CSV file must have two columns: geo_id,district"); }

        // assert CSV has correct number of rows
        if df.height() != block_layer.len() {
            bail!("[Plan.from_csv] CSV file has {} rows, expected {}", df.height(), block_layer.len());
        }

        // Populate plan.assignments from CSV
        let blocks = df.column(df.get_column_names()[0])?.cast(&DataType::String)?;
        let districts = df.column(df.get_column_names()[1])?.cast(&DataType::UInt32)?;

        let assignments = blocks.str()?.into_no_null_iter()
            .zip(districts.u32()?.into_no_null_iter())
            .map(|(block, district)| {
                let geo_id = GeoId::new(GeoType::Block, block);
                if !block_layer.geo_ids().contains(&geo_id) {
                    bail!("[Plan.from_csv] GeoId {} in CSV not found in map", geo_id.id());
                }
                Ok((geo_id, district))
            })
            .collect::<Result<_>>()?;

        self.set_assignments(assignments)
    }

    /// Generate a CSV block assignment
    pub fn to_csv(&self, path: &Path) -> Result<()> {
        let (geo_ids, districts) = self.get_assignments()?.iter()
            .filter_map(|(geo_id, &district)| (district != 0)
                .then_some((geo_id.id().to_string(), district)))
            .unzip::<_, _, Vec<_>, Vec<_>>();

        CsvWriter::new(File::create(path)?).finish(
            &mut DataFrame::new(vec![
                Series::new("geo_id".into(), geo_ids).into(),
                Series::new("district".into(), districts).into(),
            ])?
        )?;

        Ok(())
    }

    /// Randomly assign all blocks to contiguous districts.
    pub fn randomize(&mut self) -> Result<()> { Ok(self.partition.randomize()) }

    /// Equalize total weights across all districts using greedy swaps.
    pub fn equalize(&mut self, series: &str, tolerance: f64, max_iter: usize) -> Result<()> {
        if !self.partition.graph().node_weights().contains(series) {
            bail!("[Plan.equalize] Population column '{}' not found in node weights", series);
        }

        Ok(self.partition.equalize(series, tolerance, max_iter))
    }
}
