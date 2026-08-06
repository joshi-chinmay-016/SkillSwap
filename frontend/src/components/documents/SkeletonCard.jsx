import React from "react";

export function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-border/80 bg-bg p-5 shadow-xs animate-pulse flex flex-col justify-between h-44">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="w-12 h-12 rounded-xl bg-border/60" />
          <div className="w-20 h-5 rounded-full bg-border/50" />
        </div>
        <div className="h-4 w-3/4 bg-border/70 rounded-md mb-2" />
        <div className="h-3 w-1/2 bg-border/50 rounded-md" />
      </div>
      <div className="pt-3 border-t border-border/50 flex items-center justify-between">
        <div className="h-3 w-16 bg-border/50 rounded-md" />
        <div className="h-3 w-20 bg-border/50 rounded-md" />
      </div>
    </div>
  );
}

export function SkeletonGrid({ count = 8, viewMode = "grid" }) {
  if (viewMode === "list") {
    return (
      <div className="flex flex-col gap-2.5">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-16 rounded-xl border border-border/80 bg-bg p-3.5 animate-pulse flex items-center justify-between">
            <div className="flex items-center gap-3.5 flex-1">
              <div className="w-10 h-10 rounded-lg bg-border/60" />
              <div className="space-y-1.5 flex-1 max-w-sm">
                <div className="h-3.5 w-48 bg-border/70 rounded-md" />
                <div className="h-3 w-32 bg-border/50 rounded-md" />
              </div>
            </div>
            <div className="w-20 h-6 rounded-full bg-border/50 hidden sm:block" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
