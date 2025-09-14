#pragma once

#include <atomic>
#include <cstdint>
#include <functional>
#include <memory>
#include <utility>
#include <vector>

#include "hash_util.h"

namespace cmsketch {

template <typename KeyType> class CountMinSketch {
public:
  /** @brief Constructs a count-min sketch with specified dimensions
   * @param width Number of buckets
   * @param depth Number of hash functions
   */
  explicit CountMinSketch(uint32_t width, uint32_t depth);

  CountMinSketch() = delete; // Default constructor deleted
  CountMinSketch(const CountMinSketch &) = delete; // Copy constructor deleted
  auto operator=(const CountMinSketch &)
      -> CountMinSketch & = delete; // Copy assignment deleted

  CountMinSketch(CountMinSketch &&other) noexcept; // Move constructor
  auto operator=(CountMinSketch &&other) noexcept
      -> CountMinSketch &; // Move assignment

  /**
   * @brief Get the width of the sketch
   * @return Width of the sketch
   */
  auto GetWidth() const -> uint32_t { return width_; }

  /**
   * @brief Get the depth of the sketch
   * @return Depth of the sketch
   */
  auto GetDepth() const -> uint32_t { return depth_; }

  /**
   * @brief Inserts an item into the count-min sketch
   *
   * @param item The item to increment the count for
   * @note Updates the min-heap at the same time
   */
  void Insert(const KeyType &item);

  /**
   * @brief Gets the estimated count of an item
   *
   * @param item The item to look up
   * @return The estimated count
   */
  auto Count(const KeyType &item) const -> uint32_t;

  /**
   * @brief Resets the sketch to initial empty state
   *
   * @note Clears the sketch matrix, item set, and top-k min-heap
   */
  void Clear();

  /**
   * @brief Merges the current CountMinSketch with another, updating the current
   * sketch with combined data from both sketches.
   *
   * @param other The other CountMinSketch to merge with.
   * @throws std::invalid_argument if the sketches' dimensions are incompatible.
   */
  void Merge(const CountMinSketch<KeyType> &other);

  /**
   * @brief Gets the top k items based on estimated counts from a list of
   * candidates.
   *
   * @param k Number of top items to return (will be capped at initial k)
   * @param candidates List of candidate items to consider for top k
   * @return Vector of (item, count) pairs in descending count order
   */
  auto TopK(uint16_t k, const std::vector<KeyType> &candidates)
      -> std::vector<std::pair<KeyType, uint32_t>>;

private:
  /** Dimensions of the count-min sketch matrix */
  uint32_t width_; // Number of buckets for each hash function
  uint32_t depth_; // Number of independent hash functions
  /** Pre-computed hash functions for each row */
  std::vector<std::function<size_t(const KeyType &)>> hash_functions_;

  /** @fall2025 PLEASE DO NOT MODIFY THE FOLLOWING */
  constexpr static size_t SEED_BASE = 15445;

  /**
   * @brief Seeded hash function generator
   *
   * @param seed Used for creating independent hash functions
   * @return A function that maps items to column indices
   */
  inline auto HashFunction(size_t seed)
      -> std::function<size_t(const KeyType &)> {
    return [seed, this](const KeyType &item) -> size_t {
      auto h1 = std::hash<KeyType>{}(item);
      auto h2 = cmsketch::HashUtil::CombineHashes(seed, SEED_BASE);
      return cmsketch::HashUtil::CombineHashes(h1, h2) % width_;
    };
  }

  /** @todo (student) can add their data structures that support count-min
   * sketch operations */

  // A vector representing the sketch matrix
  std::unique_ptr<std::vector<std::atomic<uint32_t>>> sketch_matrix_;
};

} // namespace cmsketch
