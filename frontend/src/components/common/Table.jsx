import React from "react";

export function Table({ children, className = "", ...props }) {
  return (
    <div className="overflow-x-auto">
      <table className={`w-full text-sm ${className}`} {...props}>
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ children, className = "", ...props }) {
  return (
    <thead className={`bg-bg-alt border-b border-border ${className}`} {...props}>
      {children}
    </thead>
  );
}

export function TableBody({ children, className = "", ...props }) {
  return (
    <tbody className={className} {...props}>
      {children}
    </tbody>
  );
}

export function TableRow({ children, className = "", hoverable = true, ...props }) {
  return (
    <tr
      className={`
        border-b border-border last:border-b-0
        ${hoverable ? "hover:bg-bg-alt/50 transition-colors" : ""}
        ${className}
      `}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableHead({ children, className = "", align = "left", ...props }) {
  const alignStyles = {
    left: "text-left",
    center: "text-center",
    right: "text-right",
  };

  return (
    <th
      className={`
        px-4 py-3 text-xs font-semibold text-text-secondary uppercase tracking-wider
        ${alignStyles[align]}
        ${className}
      `}
      {...props}
    >
      {children}
    </th>
  );
}

export function TableCell({ children, className = "", align = "left", ...props }) {
  const alignStyles = {
    left: "text-left",
    center: "text-center",
    right: "text-right",
  };

  return (
    <td
      className={`
        px-4 py-3 text-text
        ${alignStyles[align]}
        ${className}
      `}
      {...props}
    >
      {children}
    </td>
  );
}

export default Table;