import React, { useState, createContext, useContext } from "react";
import { motion } from "motion/react";

const TabsContext = createContext({
  activeTab: "",
  setActiveTab: () => {},
});

export function Tabs({ children, defaultValue, value, onValueChange, className = "" }) {
  const [internalValue, setInternalValue] = useState(defaultValue);
  
  const activeTab = value !== undefined ? value : internalValue;
  const setActiveTab = onValueChange || setInternalValue;

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ children, className = "" }) {
  return (
    <div
      role="tablist"
      className={`flex gap-1 ${className}`}
    >
      {children}
    </div>
  );
}

export function TabsTrigger({ children, value, className = "", ...props }) {
  const { activeTab, setActiveTab } = useContext(TabsContext);
  const isActive = activeTab === value;

  return (
    <motion.button
      type="button"
      role="tab"
      aria-selected={isActive}
      onClick={() => setActiveTab(value)}
      className={`
        px-4 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer
        focus:outline-none focus:ring-2 focus:ring-accent/20
        ${isActive
          ? "bg-accent text-white shadow-sm"
          : "text-text-secondary hover:text-text hover:bg-bg-alt"
        }
        ${className}
      `}
      whileTap={isActive ? {} : { scale: 0.98 }}
      {...props}
    >
      {children}
    </motion.button>
  );
}

export function TabsContent({ children, value, className = "", ...props }) {
  const { activeTab } = useContext(TabsContext);
  
  if (activeTab !== value) return null;

  return (
    <motion.div
      role="tabpanel"
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export default Tabs;