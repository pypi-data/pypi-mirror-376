//! A `DigitBinIndex` is a tree-based data structure that organizes a large
//! collection of weighted items to enable highly efficient weighted random
//! selection and removal.
//!
//! It is a specialized tool, purpose-built for scenarios with millions of
//! items where probabilities are approximate and high performance is critical,
//! particularly for simulations involving sequential sampling like Wallenius'
//! noncentral hypergeometric distribution.

use rust_decimal::Decimal;
use rand::{rngs::ThreadRng, Rng};
use roaring::RoaringBitmap;
use std::vec;

// The default precision to use if none is specified in the constructor.
const DEFAULT_PRECISION: u8 = 3;
const MAX_PRECISION: usize = 10;

/// The content of a node, which is either more nodes or a leaf with individuals.
#[derive(Debug, Clone)]
pub enum NodeContent {
    /// An internal node that contains children for the next digit (0-9).
    Internal(Vec<Node>),
    /// A leaf node that contains a roaring bitmap of IDs for individuals in this bin.
    Leaf(RoaringBitmap),
}

/// A node within the DigitBinIndex tree.
#[derive(Debug, Clone)]
pub struct Node {
    /// The content of this node, either more nodes or a list of individual IDs.
    pub content: NodeContent,
    /// The total sum of probabilities stored under this node.
    pub accumulated_value: Decimal,
    /// The total count of individuals stored under this node.
    pub content_count: u32,
}

impl Node {
    /// Creates a new, empty internal node.
    fn new_internal() -> Self {
        Self {
            content: NodeContent::Internal(vec![]),
            accumulated_value: Decimal::from(0),
            content_count: 0,
        }
    }
}

/// A data structure that organizes weighted items into bins based on their
/// decimal digits to enable fast weighted random selection and updates.
///
/// This structure is a specialized radix tree optimized for sequential sampling
/// (like in Wallenius' distribution). It makes a deliberate engineering trade-off:
/// it sacrifices a small, controllable amount of precision by binning items,
/// but in return, it achieves O(P) performance for its core operations, where P
/// is the configured precision. This is significantly faster than the O(log N)
/// performance of general-purpose structures like a Fenwick Tree for its
/// ideal use case.
#[derive(Debug, Clone)]
pub struct DigitBinIndex {
    /// The root node of the tree.
    pub root: Node,
    /// The precision (number of decimal places) used for binning.
    pub precision: u8,
    // For weight_to_digits
    powers: [u128; MAX_PRECISION], 
}

impl Default for DigitBinIndex {
    fn default() -> Self {
        Self::new()
    }
}

impl DigitBinIndex {
    /// Creates a new `DigitBinIndex` instance with the default precision.
    ///
    /// The default precision is set to 3 decimal places, which provides a good balance
    /// between accuracy and performance for most use cases. For custom precision, use
    /// [`with_precision`](Self::with_precision).
    ///
    /// # Returns
    ///
    /// A new `DigitBinIndex` instance.
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    ///
    /// let index = DigitBinIndex::new();
    /// assert_eq!(index.precision, 3);
    /// ```    
    #[must_use]
    pub fn new() -> Self {
        Self::with_precision(DEFAULT_PRECISION)
    }

    /// Creates a new `DigitBinIndex` instance with the specified precision.
    ///
    /// The precision determines the number of decimal places used for binning weights.
    /// Higher precision improves sampling accuracy but increases memory usage and tree depth.
    /// Precision must be between 1 and 10 (inclusive).
    ///
    /// # Arguments
    ///
    /// * `precision` - The number of decimal places for binning (1 to 10).
    ///
    /// # Returns
    ///
    /// A new `DigitBinIndex` instance with the given precision.
    ///
    /// # Panics
    ///
    /// Panics if `precision` is 0 or greater than 10.
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    ///
    /// let index = DigitBinIndex::with_precision(4);
    /// assert_eq!(index.precision, 4);
    /// ```
    #[must_use]
    pub fn with_precision(precision: u8) -> Self {
        assert!(precision > 0, "Precision must be at least 1.");
        assert!(precision <= MAX_PRECISION as u8, "Precision cannot be larger than {}.", MAX_PRECISION);
        let mut powers = [0u128; MAX_PRECISION];
        for i in 0..MAX_PRECISION {
            powers[i] = 10u128.pow(i as u32)
        }
        Self {
            root: Node::new_internal(),
            precision,
            powers,
        }        
    }

    /// Converts a Decimal weight to an array of digits [0-9] for the given precision.
    /// Returns None if the weight is invalid (non-positive or zero after scaling).
    fn weight_to_digits(&self, weight: Decimal) -> Option<[u8; MAX_PRECISION]> {
        if weight <= Decimal::ZERO {
            return None;
        }

        // Rescale to desired precision
        let mut scaled = weight;
        scaled.rescale(self.precision as u32);
        if scaled.is_zero() {
            return None;
        }

        let mut digits = [0u8; MAX_PRECISION];
        let scale = scaled.scale() as usize;
        let mantissa = scaled.mantissa().abs() as u128;

        // Extract digits from mantissa
        for i in 0..self.precision as usize {
            if i >= scale {
                digits[i] = 0; // Pad with zeros for less precise numbers
            } else {
                digits[i] = ((mantissa / self.powers[scale - i]) % 10) as u8;
            }
        }
        Some(digits)
    }

    // --- Standard Functions ---

    /// Adds an item with the given ID and weight to the index.
    ///
    /// The weight is rescaled to the index's precision and binned accordingly.
    /// If the weight is non-positive or becomes zero after scaling, the item is not added.
    ///
    /// # Arguments
    ///
    /// * `individual_id` - The unique ID of the item to add (u32).
    /// * `weight` - The positive weight (probability) of the item.
    ///
    /// # Returns
    ///
    /// `true` if the item was successfully added, `false` otherwise (e.g., invalid weight).
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    /// use rust_decimal_macros::dec;
    ///
    /// let mut index = DigitBinIndex::new();
    /// let added = index.add(1, dec!(0.5));
    /// assert!(added);
    /// assert_eq!(index.count(), 1);
    /// ```    
    pub fn add(&mut self, individual_id: u32, mut weight: Decimal) -> bool {
        if let Some(digits) = self.weight_to_digits(weight) {
            weight.rescale(self.precision as u32);
            Self::add_recurse(&mut self.root, individual_id, weight, &digits, 1, self.precision);
            true
        } else {
            false
        }
    }

    /// Recursive private method to handle adding individuals.
    fn add_recurse(
        node: &mut Node,
        individual_id: u32,
        weight: Decimal, // Still needed for accumulated_value
        digits: &[u8; MAX_PRECISION],
        current_depth: u8,
        max_depth: u8,
    ) {
        node.content_count += 1;
        node.accumulated_value += weight;

        if current_depth > max_depth {
            if let NodeContent::Internal(_) = &node.content {
                node.content = NodeContent::Leaf(RoaringBitmap::new());
            }
            if let NodeContent::Leaf(bitmap) = &mut node.content {
                bitmap.insert(individual_id);
            }
            return;
        }

        let digit = digits[current_depth as usize - 1] as usize;
        if let NodeContent::Internal(children) = &mut node.content {
            if children.len() <= digit {
                children.resize_with(digit + 1, Node::new_internal);
            }
            Self::add_recurse(&mut children[digit], individual_id, weight, digits, current_depth + 1, max_depth);
        }
    }

    /// Removes an item with the given ID and weight from the index.
    ///
    /// The weight must match the one used during addition (after rescaling).
    /// If the item is not found in the corresponding bin, no removal occurs.
    ///
    /// # Arguments
    ///
    /// * `individual_id` - The ID of the item to remove.
    /// * `weight` - The weight of the item (must match the added weight).
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    /// use rust_decimal_macros::dec;
    ///
    /// let mut index = DigitBinIndex::new();
    /// index.add(1, dec!(0.5));
    /// index.remove(1, dec!(0.5));
    /// assert_eq!(index.count(), 0);
    /// ```
    pub fn remove(&mut self, individual_id: u32, mut weight: Decimal) {
        if let Some(digits) = self.weight_to_digits(weight) {
            weight.rescale(self.precision as u32);
            self.remove_with_digits(individual_id, weight, digits);
        }
    }

    // Helper function
    fn remove_with_digits(&mut self, individual_id: u32, weight: Decimal, digits: [u8; MAX_PRECISION]) {
        Self::remove_recurse(&mut self.root, individual_id, weight, &digits, 1, self.precision);
    }

    /// Recursive private method to handle removing individuals.
    fn remove_recurse(
        node: &mut Node,
        individual_id: u32,
        weight: Decimal,
        digits: &[u8; MAX_PRECISION],
        current_depth: u8,
        max_depth: u8,
    ) -> bool {
        if current_depth > max_depth {
            if let NodeContent::Leaf(bitmap) = &mut node.content {
                if bitmap.remove(individual_id) {
                    node.content_count -= 1;
                    node.accumulated_value -= weight;
                    return true;
                }
            }
            return false;
        }

        let digit = digits[current_depth as usize - 1] as usize;
        if let NodeContent::Internal(children) = &mut node.content {
            if children.len() > digit && Self::remove_recurse(&mut children[digit], individual_id, weight, digits, current_depth + 1, max_depth) {
                node.content_count -= 1;
                node.accumulated_value -= weight;
                return true;
            }
        }
        false
    }


    // --- Selection Functions ---

    /// Selects a single item randomly based on weights without removal.
    ///
    /// Performs weighted random selection. Returns `None` if the index is empty.
    ///
    /// # Returns
    ///
    /// An `Option` containing the selected item's ID and its (rescaled) weight.
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    /// use rust_decimal_macros::dec;
    ///
    /// let mut index = DigitBinIndex::new();
    /// index.add(1, dec!(0.5));
    /// if let Some((id, weight)) = index.select() {
    ///     assert_eq!(id, 1);
    ///     assert_eq!(weight, dec!(0.500));
    /// }
    /// ```
    pub fn select(&mut self) -> Option<(u32, Decimal)> {
        self.select_and_optionally_remove(false)
    }

    /// Selects multiple unique items randomly based on weights without removal.
    ///
    /// Uses rejection sampling to ensure uniqueness. Returns `None` if `num_to_draw`
    /// exceeds the number of items in the index.
    ///
    /// # Arguments
    ///
    /// * `num_to_draw` - The number of unique items to select.
    ///
    /// # Returns
    ///
    /// An `Option` containing a vector of selected (ID, weight) pairs.
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    /// use rust_decimal_macros::dec;
    ///
    /// let mut index = DigitBinIndex::new();
    /// index.add(1, dec!(0.3));
    /// index.add(2, dec!(0.7));
    /// if let Some(selected) = index.select_many(2) {
    ///     assert_eq!(selected.len(), 2);
    /// }
    /// ```
    pub fn select_many(&mut self, num_to_draw: u32) -> Option<Vec<(u32, Decimal)>> {
        self.select_many_and_optionally_remove(num_to_draw, false)
    }

    /// Selects a single item randomly and removes it from the index.
    ///
    /// Combines selection and removal in one operation. Returns `None` if empty.
    ///
    /// # Returns
    ///
    /// An `Option` containing the selected item's ID and weight.
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    /// use rust_decimal_macros::dec;
    ///
    /// let mut index = DigitBinIndex::new();
    /// index.add(1, dec!(0.5));
    /// if let Some((id, _)) = index.select_and_remove() {
    ///     assert_eq!(id, 1);
    /// }
    /// assert_eq!(index.count(), 0);
    /// ```
    pub fn select_and_remove(&mut self) -> Option<(u32, Decimal)> {
        self.select_and_optionally_remove(true)
    }

    // Wrapper function to handle both select and select_and_remove
    pub fn select_and_optionally_remove(&mut self, with_removal: bool) -> Option<(u32, Decimal)> {
        if self.root.content_count == 0 {
            return None;
        }
        let mut rng = rand::thread_rng();
        let random_target = rng.gen_range(Decimal::ZERO..self.root.accumulated_value);
        Self::select_and_optionally_remove_recurse(&mut self.root, random_target, 1, self.precision, &mut rng, with_removal)
    }

    // Helper function
    fn select_and_optionally_remove_recurse(
        node: &mut Node,
        mut target: Decimal,
        current_depth: u8,
        max_depth: u8,
        rng: &mut ThreadRng,
        with_removal: bool,
    ) -> Option<(u32, Decimal)> {
        // Base case: Leaf node
        if current_depth > max_depth {
            if let NodeContent::Leaf(bitmap) = &mut node.content {
                if bitmap.is_empty() {
                    return None;
                }
                let rand_index = rng.gen_range(0..node.content_count);
                if let Some(selected_id) = bitmap.select(rand_index) {
                    let weight = node.accumulated_value / Decimal::from(node.content_count);
                    if with_removal {
                        bitmap.remove(selected_id);
                        node.content_count -= 1;
                        node.accumulated_value -= weight;
                    }
                    return Some((selected_id, weight));
                }
            }
            return None;
        }

        // Recursive case: Internal node
        if let NodeContent::Internal(children) = &mut node.content {
            for child in children.iter_mut() {
                if child.accumulated_value.is_zero() {
                    continue;
                }
                if target < child.accumulated_value {
                    if let Some((selected_id, weight)) = Self::select_and_optionally_remove_recurse(
                        child,
                        target,
                        current_depth + 1,
                        max_depth,
                        rng,
                        with_removal,
                    ) {
                        if with_removal {
                            node.content_count -= 1;
                            node.accumulated_value -= weight;
                        }
                        return Some((selected_id, weight));
                    }
                    return None; // If recurse failed (e.g., empty after skip), but shouldn't happen
                }
                target -= child.accumulated_value;
            }
        }
        None
    } 

    /// Selects multiple unique items randomly and removes them from the index.
    ///
    /// Selects and removes in batch. Returns `None` if `num_to_draw` exceeds item count.
    ///
    /// # Arguments
    ///
    /// * `num_to_draw` - The number of unique items to select and remove.
    ///
    /// # Returns
    ///
    /// An `Option` containing a vector of selected (ID, weight) pairs.
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    /// use rust_decimal_macros::dec;
    ///
    /// let mut index = DigitBinIndex::new();
    /// index.add(1, dec!(0.3));
    /// index.add(2, dec!(0.7));
    /// if let Some(selected) = index.select_many_and_remove(2) {
    ///     assert_eq!(selected.len(), 2);
    /// }
    /// assert_eq!(index.count(), 0);
    /// ```
    pub fn select_many_and_remove(&mut self, num_to_draw: u32) -> Option<Vec<(u32, Decimal)>> {
        self.select_many_and_optionally_remove(num_to_draw, true)
    }

    // Wrapper function to handle both select_many and select_many_and_remove
    pub fn select_many_and_optionally_remove(&mut self, num_to_draw: u32, with_removal: bool) -> Option<Vec<(u32, Decimal)>> {
        if num_to_draw > self.count() || num_to_draw == 0 {
            return if num_to_draw == 0 { Some(Vec::new()) } else { None };
        }
        let mut rng = rand::thread_rng();
        let mut selected = Vec::with_capacity(num_to_draw as usize);
        let total_weight = self.root.accumulated_value;
        // Pass precision explicitly to avoid needing self in the recursive function
        Self::select_many_and_optionally_remove_recurse(
            &mut self.root,
            num_to_draw,
            total_weight,
            &mut selected,
            &mut rng,
            1,
            self.precision,
            with_removal,
        );
        if selected.len() == num_to_draw as usize {
            Some(selected)
        } else {
            None // Should not happen if logic is correct
        }
    }

    /// Recursive helper for batch selection and removal.
    /// - node: Current subtree root.
    /// - m: Number to select from this subtree.
    /// - subtree_total: Accumulated weight of this node.
    /// - selected: Mutable vec to collect (id, weight) from leaves.
    /// - rng: Mutable RNG.
    /// - current_depth: Current digit level.
    /// - precision: The precision of the DigitBinIndex (passed explicitly).
    fn select_many_and_optionally_remove_recurse(
        node: &mut Node,
        m: u32,
        subtree_total: Decimal,
        selected: &mut Vec<(u32, Decimal)>,
        rng: &mut ThreadRng,
        current_depth: u8,
        precision: u8,
        with_removal: bool,
    ) {
        if m == 0 {
            return;
        }
        if current_depth > precision {
            // Leaf: Pick m random unique IDs from bitmap.
            if let NodeContent::Leaf(bitmap) = &mut node.content {
                let bin_weight = if node.content_count > 0 {
                    node.accumulated_value / Decimal::from(node.content_count)
                } else {
                    Decimal::ZERO
                };
                let mut picked = 0;
                while picked < m && !bitmap.is_empty() {
                    let rand_index = rng.gen_range(0..bitmap.len() as u32);
                    if let Some(id) = bitmap.select(rand_index) {
                        if with_removal {
                            bitmap.remove(id);
                        }
                        selected.push((id, bin_weight));
                        picked += 1;
                    }
                }
                if with_removal {
                    // Update node
                    node.content_count -= picked;
                    node.accumulated_value -= bin_weight * Decimal::from(picked);
                }
            }
            return;
        }

        // Internal node: Assign m selections to children with rejection.
        if let NodeContent::Internal(children) = &mut node.content {
            // Prepare per-child data: assigned counts and lists of relative targets for reuse.
            let mut child_assigned = vec![0u32; children.len()];
            let mut child_rel_targets: Vec<Vec<Decimal>> = vec![Vec::new(); children.len()];

            let mut assigned = 0u32;
            while assigned < m {
                let target = rng.gen_range(Decimal::ZERO..subtree_total);
                let mut cum = Decimal::ZERO;
                let mut chosen_child = None;
                for (i, child) in children.iter().enumerate() {
                    if target < cum + child.accumulated_value {
                        if child_assigned[i] + 1 <= child.content_count {
                            chosen_child = Some(i);
                        }
                        break;
                    }
                    cum += child.accumulated_value;
                }
                if let Some(idx) = chosen_child {
                    child_assigned[idx] += 1;
                    // Compute relative target for reuse in sub-level: target - cum_before_this_child
                    let rel_target = target - (cum - children[idx].accumulated_value);
                    child_rel_targets[idx].push(rel_target);
                    assigned += 1;
                }
                // Else: reject (redraw loop continues)
            }

            // Recurse into each child with assigned > 0, passing precision
            for (i, child) in children.iter_mut().enumerate() {
                let child_m = child_assigned[i];
                if child_m > 0 {
                    Self::select_many_and_optionally_remove_recurse(
                        child,
                        child_m,
                        child.accumulated_value,
                        selected,
                        rng,
                        current_depth + 1,
                        precision,
                        with_removal,
                    );
                }
            }

            if with_removal {
                // On unwind: Update this node's counts and values based on what was removed below
                node.content_count = children.iter().map(|c| c.content_count).sum();
                node.accumulated_value = children.iter().map(|c| c.accumulated_value).sum();
            }
        }
    }


    /// Returns the total number of items currently in the index.
    ///
    /// # Returns
    ///
    /// The count of items as a `u32`.
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    ///
    /// let mut index = DigitBinIndex::new();
    /// assert_eq!(index.count(), 0);
    /// ```
    pub fn count(&self) -> u32 {
        self.root.content_count
    }

    /// Returns the sum of all weights in the index.
    ///
    /// This represents the total accumulated probability mass.
    ///
    /// # Returns
    ///
    /// The total weight as a `Decimal`.
    ///
    /// # Examples
    ///
    /// ```
    /// use digit_bin_index::DigitBinIndex;
    /// use rust_decimal_macros::dec;
    ///
    /// let mut index = DigitBinIndex::new();
    /// index.add(1, dec!(0.5));
    /// assert_eq!(index.total_weight(), dec!(0.500));
    /// ```
    pub fn total_weight(&self) -> Decimal {
        self.root.accumulated_value
    }
}

#[cfg(feature = "python-bindings")]
mod python {
    use super::*;
    use pyo3::prelude::*;
    use rust_decimal::prelude::FromPrimitive;

    #[pyclass(name = "DigitBinIndex")]
    struct PyDigitBinIndex {
        index: DigitBinIndex,
    }

    #[pymethods]
    impl PyDigitBinIndex {
        #[new]
        fn new(precision: u32) -> Self {
            PyDigitBinIndex {
                index: DigitBinIndex::with_precision(precision.try_into().unwrap()),
            }
        }

        fn add(&mut self, id: u32, weight: f64) -> bool {
            if let Some(decimal_weight) = Decimal::from_f64(weight) {
                self.index.add(id, decimal_weight)
            } else {
                false
            }
        }

        fn remove(&mut self, id: u32, weight: f64) {
            if let Some(decimal_weight) = Decimal::from_f64(weight) {
                self.index.remove(id, decimal_weight);
            }
        }

        fn select(&mut self) -> Option<(u32, String)> {
            self.index.select().map(|(id, weight)| (id, weight.to_string()))
        }

        fn select_many(&mut self, n: u32) -> Option<Vec<(u32, String)>> {
            self.index.select_many(n).map(|items| {
                items.into_iter().map(|(id, w)| (id, w.to_string())).collect()
            })
        }

        fn select_and_remove(&mut self) -> Option<(u32, String)> {
            self.index.select_and_remove().map(|(id, weight)| (id, weight.to_string()))
        }

        fn select_many_and_remove(&mut self, n: u32) -> Option<Vec<(u32, String)>> {
            self.index.select_many_and_remove(n).map(|items| {
                items.into_iter().map(|(id, w)| (id, w.to_string())).collect()
            })
        }

        fn count(&self) -> u32 {
            self.index.count()
        }

        fn total_weight(&self) -> String {
            self.index.total_weight().to_string()
        }
    }

    #[pymodule]
    fn digit_bin_index(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_class::<PyDigitBinIndex>()?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rust_decimal_macros::dec;

    #[test]
    fn test_select_and_remove() {
        let mut index = DigitBinIndex::with_precision(3);
        index.add(1, dec!(0.085));
        index.add(2, dec!(0.205));
        index.add(3, dec!(0.346));
        index.add(4, dec!(0.364));
        println!("Initial state: {} individuals, total weight = {}", index.count(), index.total_weight());    
        if let Some((id, weight)) = index.select_and_remove() {
            println!("Selected ID: {} with weight: {}", id, weight);
        }
        assert!(
            index.count() == 3,
            "The count is now {} and not 3 as expected",
            index.count()
        );
        println!("Intermediate state: {} individuals, total weight = {}", index.count(), index.total_weight()); 
        if let Some(selection) = index.select_many_and_remove(2) {
            println!("Selection: {:?}", selection);
        }
        assert!(
            index.count() == 1,
            "The count is now {} and not 1 as expected",
            index.count()
        );
        println!("Final state: {} individuals, total weight = {}", index.count(), index.total_weight()); 
    }

    #[test]
    fn test_wallenius_distribution_is_correct() {
        // --- Setup: Create a controlled population ---
        const ITEMS_PER_GROUP: u32 = 1000;
        const TOTAL_ITEMS: u32 = ITEMS_PER_GROUP * 2;
        const NUM_DRAWS: u32 = TOTAL_ITEMS / 2;

        let low_risk_weight = dec!(0.1);  // 0.1
        let high_risk_weight = dec!(0.2); // 0.2

        // --- Execution: Run many simulations to average out randomness ---
        const NUM_SIMULATIONS: u32 = 100;
        let mut total_high_risk_selected = 0;

        for _ in 0..NUM_SIMULATIONS {
            let mut index = DigitBinIndex::with_precision(3);
            for i in 0..ITEMS_PER_GROUP { index.add(i, low_risk_weight); }
            for i in ITEMS_PER_GROUP..TOTAL_ITEMS { index.add(i, high_risk_weight); }

            let mut high_risk_in_this_run = 0;
            for _ in 0..NUM_DRAWS {
                if let Some((selected_id, _)) = index.select_and_remove() {
                    if selected_id >= ITEMS_PER_GROUP {
                        high_risk_in_this_run += 1;
                    }
                }
            }
            total_high_risk_selected += high_risk_in_this_run;
        }

        // --- Validation: Check the statistical properties of a Wallenius' draw ---
        let avg_high_risk = total_high_risk_selected as f64 / NUM_SIMULATIONS as f64;

        // 1. The mean of a uniform draw (central hypergeometric) would be 500.
        let uniform_mean = NUM_DRAWS as f64 * 0.5;

        // 2. The mean of a simultaneous draw (Fisher's NCG) is based on initial proportions.
        // This is the naive expectation we started with.
        let fishers_mean = NUM_DRAWS as f64 * (2.0 / 3.0); // ~666.67

        // The mean of a Wallenius' draw is mathematically proven to lie strictly
        // between the uniform mean and the Fisher's mean.
        assert!(
            avg_high_risk > uniform_mean,
            "Test failed: Result {:.2} was not biased towards higher weights (uniform mean is {:.2})",
            avg_high_risk, uniform_mean
        );

        assert!(
            avg_high_risk < fishers_mean,
            "Test failed: Result {:.2} showed too much bias. It should be less than the Fisher's mean of {:.2} due to the Wallenius effect.",
            avg_high_risk, fishers_mean
        );

        println!(
            "Distribution test passed: Got an average of {:.2} high-risk selections.",
            avg_high_risk
        );
        println!(
            "This correctly lies between the uniform mean ({:.2}) and the Fisher's mean ({:.2}), confirming the Wallenius' distribution behavior.",
            uniform_mean, fishers_mean
        );
    }
    #[test]
    fn test_fisher_distribution_is_correct() {
        const ITEMS_PER_GROUP: u32 = 1000;
        const TOTAL_ITEMS: u32 = ITEMS_PER_GROUP * 2;
        const NUM_DRAWS: u32 = TOTAL_ITEMS / 2;

        let low_risk_weight = dec!(0.1);  // 0.1
        let high_risk_weight = dec!(0.2); // 0.2

        const NUM_SIMULATIONS: u32 = 100;
        let mut total_high_risk_selected = 0;

        for _ in 0..NUM_SIMULATIONS {
            let mut index = DigitBinIndex::with_precision(3);
            for i in 0..ITEMS_PER_GROUP { index.add(i, low_risk_weight); }
            for i in ITEMS_PER_GROUP..TOTAL_ITEMS { index.add(i, high_risk_weight); }
            
            // Call the new method
            if let Some(selected_ids) = index.select_many_and_remove(NUM_DRAWS) {
                let high_risk_in_this_run = selected_ids.iter().filter(|&&(id, _)| id >= ITEMS_PER_GROUP).count();
                total_high_risk_selected += high_risk_in_this_run as u32;
            }
        }
        
        let avg_high_risk = total_high_risk_selected as f64 / NUM_SIMULATIONS as f64;
        let fishers_mean = NUM_DRAWS as f64 * (2.0 / 3.0);
        let tolerance = fishers_mean * 0.02;

        // The mean of a Fisher's draw should be very close to the naive expectation.
        assert!(
            (avg_high_risk - fishers_mean).abs() < tolerance,
            "Fisher's test failed: Result {:.2} was not close to the expected mean of {:.2}",
            avg_high_risk, fishers_mean
        );
        
        println!(
            "Fisher's test passed: Got avg {:.2} high-risk selections (expected ~{:.2}).",
            avg_high_risk, fishers_mean
        );
    }
}