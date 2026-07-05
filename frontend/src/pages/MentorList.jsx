import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api";
import MentorCard from "../components/MentorCard";
import Input from "../components/common/Input";
import Button from "../components/common/Button";
import { Search, SlidersHorizontal, AlertCircle } from "lucide-react";

export default function MentorList() {
  const [searchQuery, setSearchQuery] = useState("");
  const [skillParam, setSkillParam] = useState("");
  const [minRating, setMinRating] = useState("");
  
  const navigate = useNavigate();

  // Fetch mentors with search and rating filters
  const { data: mentors = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["mentors", skillParam, minRating],
    queryFn: async () => {
      const params = {};
      if (skillParam) params.skill = skillParam;
      if (minRating) params.min_rating = parseFloat(minRating);
      
      const res = await api.get("/mentors/", { params });
      return res.data;
    },
  });

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setSkillParam(searchQuery);
  };

  const handleClearFilters = () => {
    setSearchQuery("");
    setSkillParam("");
    setMinRating("");
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header section */}
      <div className="text-left">
        <h1 className="text-xl md:text-2xl font-bold tracking-tight text-text m-0">
          Find a Peer Mentor
        </h1>
        <p className="text-xs text-text-secondary mt-1">
          Search for student mentors by skill and schedule a 1-on-1 swap session
        </p>
      </div>

      {/* Search and Filters Bar */}
      <Card className="bg-bg border border-border p-4 shadow-xs">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="flex-1 relative">
            <Input
              type="text"
              placeholder="Search skills (e.g. React, Python, UI/UX)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="w-full md:w-48 flex flex-col gap-1 text-left">
            <select
              value={minRating}
              onChange={(e) => setMinRating(e.target.value)}
              className="w-full h-[38px] px-3 py-2 text-sm rounded-md border border-border bg-bg text-text shadow-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent cursor-pointer"
            >
              <option value="">All Ratings</option>
              <option value="4.5">★ 4.5 & up</option>
              <option value="4.0">★ 4.0 & up</option>
              <option value="3.0">★ 3.0 & up</option>
            </select>
          </div>

          <div className="flex gap-2">
            <Button type="submit" variant="primary" className="h-[38px] px-5">
              <Search size={16} /> Search
            </Button>
            {(skillParam || minRating) && (
              <Button type="button" variant="outline" onClick={handleClearFilters} className="h-[38px]">
                Clear
              </Button>
            )}
          </div>
        </form>
      </Card>

      {/* Content Section */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-44 w-full bg-border/40 animate-pulse rounded-lg border border-border" />
          ))}
        </div>
      ) : isError ? (
        <div className="py-12 bg-bg border border-border rounded-xl flex flex-col items-center gap-2">
          <AlertCircle className="text-danger" size={32} />
          <p className="font-semibold text-sm">Failed to load mentors</p>
          <p className="text-xs text-text-secondary">Please check your backend server connection.</p>
          <Button size="sm" variant="outline" onClick={() => refetch()} className="mt-2">
            Retry
          </Button>
        </div>
      ) : mentors.length === 0 ? (
        <div className="py-16 bg-bg border border-border rounded-xl flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-bg-alt flex items-center justify-center text-text-secondary border border-border">
            <Search size={20} />
          </div>
          <p className="font-semibold text-sm">No mentors found</p>
          <p className="text-xs text-text-secondary max-w-sm text-center">
            We couldn't find any mentors matching "{skillParam || searchQuery}". Try searching for another skill or clearing filters.
          </p>
          <Button size="sm" variant="outline" onClick={handleClearFilters} className="mt-2">
            Clear Filters
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mentors.map((mentor) => (
            <MentorCard
              key={mentor.mentor_id}
              mentor={mentor}
              onClick={() =>
                navigate(`/mentors/${mentor.mentor_id}`, {
                  state: { mentorName: mentor.mentor_name, averageRating: mentor.average_rating },
                })
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Dummy Card helper for embedding search form inside layout cleanly
function Card({ children, className = "", ...props }) {
  return (
    <div className={`rounded-lg border border-border bg-bg-alt text-text p-4 ${className}`} {...props}>
      {children}
    </div>
  );
}
