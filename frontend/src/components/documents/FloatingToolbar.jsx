import React from "react";
import SearchBar from "./SearchBar";
import FilterPills from "./FilterPills";
import StatusFilters from "./StatusFilters";
import SortDropdown from "./SortDropdown";
import ViewToggle from "./ViewToggle";

export default function FloatingToolbar({
  searchQuery,
  onSearchChange,
  selectedFilter,
  onFilterChange,
  selectedStatus,
  onStatusChange,
  selectedSort,
  onSortChange,
  viewMode,
  onViewModeChange,
}) {
  return (
    <div className="sticky top-2 z-30 my-4 rounded-2xl border border-border/80 bg-surface/80 backdrop-blur-xl p-3 shadow-lg space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Search Bar */}
        <SearchBar value={searchQuery} onChange={onSearchChange} />

        {/* Extension Filter Pills */}
        <FilterPills selectedFilter={selectedFilter} onSelectFilter={onFilterChange} />

        {/* Sort & View Controls */}
        <div className="flex items-center gap-2">
          <SortDropdown selectedSort={selectedSort} onSelectSort={onSortChange} />
          <ViewToggle viewMode={viewMode} onChangeViewMode={onViewModeChange} />
        </div>
      </div>

      {/* Status Chips Row */}
      <div className="pt-2 border-t border-border/50">
        <StatusFilters selectedStatus={selectedStatus} onStatusChange={onStatusChange} />
      </div>
    </div>
  );
}
