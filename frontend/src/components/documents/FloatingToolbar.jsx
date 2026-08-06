import React from "react";
import SearchBar from "./SearchBar";
import FilterPills from "./FilterPills";
import SortDropdown from "./SortDropdown";
import ViewToggle from "./ViewToggle";

export default function FloatingToolbar({
  searchQuery,
  onSearchChange,
  selectedFilter,
  onFilterChange,
  selectedSort,
  onSortChange,
  viewMode,
  onViewModeChange,
}) {
  return (
    <div className="sticky top-2 z-30 my-4 rounded-2xl border border-border/80 bg-bg/80 backdrop-blur-md p-3 shadow-md flex flex-wrap items-center justify-between gap-3">
      {/* Search Bar */}
      <SearchBar value={searchQuery} onChange={onSearchChange} />

      {/* Filter Pills */}
      <FilterPills selectedFilter={selectedFilter} onSelectFilter={onFilterChange} />

      {/* Sort & View Controls */}
      <div className="flex items-center gap-2">
        <SortDropdown selectedSort={selectedSort} onSelectSort={onSortChange} />
        <ViewToggle viewMode={viewMode} onChangeViewMode={onViewModeChange} />
      </div>
    </div>
  );
}
