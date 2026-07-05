import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ChevronDown, Check } from "lucide-react";

export default function Select({
  options = [],
  value,
  onChange,
  placeholder = "Select an option",
  disabled = false,
  error,
  label,
  className = "",
  size = "md",
  ...props
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const containerRef = useRef(null);

  const sizes = {
    sm: "px-2.5 py-1.5 text-xs gap-1.5",
    md: "px-3 py-2 text-sm gap-2",
    lg: "px-4 py-2.5 text-base gap-2.5",
  };

  const selectedOption = options.find((opt) => opt.value === value);

  const filteredOptions = options.filter((opt) =>
    opt.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (optionValue) => {
    onChange?.(optionValue);
    setIsOpen(false);
    setSearchTerm("");
  };

  const toggleOpen = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
    }
  };

  return (
    <div className={`flex flex-col gap-1.5 ${className}`} ref={containerRef} {...props}>
      {label && (
        <label className="text-xs font-semibold text-text-secondary">
          {label}
        </label>
      )}
      
      <div className="relative">
        <button
          type="button"
          role="combobox"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          disabled={disabled}
          onClick={toggleOpen}
          className={`
            w-full flex items-center justify-between bg-bg border rounded-md 
            transition-colors cursor-pointer
            ${sizes[size]}
            ${error ? "border-danger focus:border-danger" : "border-border focus:border-accent"}
            ${disabled ? "opacity-50 cursor-not-allowed bg-bg-alt" : "hover:border-accent/40"}
            focus:outline-none focus:ring-2 focus:ring-accent/20
          `}
        >
          <span className={`flex-1 text-left ${!selectedOption ? "text-text-secondary" : "text-text"}`}>
            {selectedOption?.label || placeholder}
          </span>
          <ChevronDown
            size={14}
            className={`text-text-secondary transition-transform duration-150 ${isOpen ? "rotate-180" : ""}`}
          />
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.1 }}
              className="absolute z-50 w-full mt-1 bg-bg border border-border rounded-md shadow-lg max-h-48 overflow-hidden"
            >
              {options.length > 6 && (
                <div className="p-2 border-b border-border">
                  <input
                    type="text"
                    placeholder="Search..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    className="w-full px-2 py-1.5 text-xs bg-bg-alt border border-border rounded-md text-text placeholder:text-text-secondary focus:outline-none focus:border-accent"
                  />
                </div>
              )}
              
              <ul role="listbox" className="py-1 overflow-y-auto">
                {filteredOptions.length === 0 ? (
                  <li className="px-3 py-2 text-xs text-text-secondary text-center">
                    No options found
                  </li>
                ) : (
                  filteredOptions.map((option) => (
                    <li key={option.value}>
                      <button
                        type="button"
                        role="option"
                        aria-selected={option.value === value}
                        onClick={() => handleSelect(option.value)}
                        className={`
                          w-full flex items-center gap-2 px-3 py-2 text-sm text-left
                          transition-colors cursor-pointer
                          ${option.value === value
                            ? "bg-accent/10 text-accent font-medium"
                            : "text-text hover:bg-bg-alt"
                          }
                        `}
                      >
                        {option.value === value && <Check size={14} />}
                        <span className={option.value === value ? "" : "ml-6"}>
                          {option.label}
                        </span>
                      </button>
                    </li>
                  ))
                )}
              </ul>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {error && (
        <p className="text-xs text-danger mt-0.5">{error}</p>
      )}
    </div>
  );
}