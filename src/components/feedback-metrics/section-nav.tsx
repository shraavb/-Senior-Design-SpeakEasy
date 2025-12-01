import { useEffect, useState, useRef } from "react";
import { Mic, BookOpen, AlertCircle, BookMarked } from "lucide-react";
import { cn } from "@/lib/utils";

interface Section {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const sections: Section[] = [
  { id: "fluency", label: "Fluency & Pronunciation", icon: Mic },
  { id: "grammar", label: "Grammar Feedback", icon: BookOpen },
  { id: "errors", label: "Error Breakdown", icon: AlertCircle },
  { id: "vocabulary", label: "Vocabulary Insights", icon: BookMarked },
];

interface SectionNavProps {
  activeSection: string;
  onSectionChange: (sectionId: string) => void;
  timeFilter: "today" | "weekly" | "monthly";
  onTimeFilterChange: (filter: "today" | "weekly" | "monthly") => void;
}

export function SectionNav({ 
  activeSection, 
  onSectionChange,
  timeFilter,
  onTimeFilterChange 
}: SectionNavProps) {
  const [isSticky, setIsSticky] = useState(false);
  const navRef = useRef<HTMLElement>(null);
  const placeholderRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const stickyThresholdRef = useRef<number | null>(null);
  const rafIdRef = useRef<number | null>(null);
  const navHeightRef = useRef<number | null>(null);
  const isStickyRef = useRef(false);

  // Initialize the sticky threshold once on mount
  useEffect(() => {
    isStickyRef.current = false;
    
    const calculateThreshold = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        stickyThresholdRef.current = rect.top + window.scrollY;
      }
    };
    
    // Calculate after a brief delay to ensure layout is settled
    const timer = setTimeout(calculateThreshold, 100);
    calculateThreshold();
    
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const updateStickyState = () => {
      if (stickyThresholdRef.current === null || !navRef.current) {
        return;
      }
      
      const scrollY = window.scrollY || window.pageYOffset;
      // Use larger hysteresis: different thresholds to prevent rapid toggling and snapping
      // Sticky when scrolled past threshold, unsticky when scrolled back above threshold - 50px
      // Larger buffer prevents snapping when scrolling back up
      const threshold = stickyThresholdRef.current;
      const currentSticky = isStickyRef.current;
      const shouldBeSticky = currentSticky 
        ? scrollY > threshold - 50  // Once sticky, need to scroll back up more to unstick (larger buffer)
        : scrollY >= threshold;      // To become sticky, just need to reach threshold
      
      if (shouldBeSticky !== currentSticky) {
        // Capture height before state change if becoming sticky
        if (shouldBeSticky && navRef.current && navHeightRef.current === null) {
          navHeightRef.current = navRef.current.offsetHeight;
        }
        
        isStickyRef.current = shouldBeSticky;
        setIsSticky(shouldBeSticky);
        
        // Set placeholder height when becoming sticky to prevent layout shift
        // Use requestAnimationFrame to ensure smooth transition
        requestAnimationFrame(() => {
          if (shouldBeSticky && placeholderRef.current && navHeightRef.current !== null) {
            placeholderRef.current.style.height = `${navHeightRef.current}px`;
          } else if (!shouldBeSticky && placeholderRef.current) {
            // Smoothly transition to 0
            placeholderRef.current.style.height = '0px';
            // Reset height ref after transition completes
            setTimeout(() => {
              navHeightRef.current = null;
            }, 300); // Match transition duration
          }
        });
      }
      
      // Update height reference if nav is not sticky (in case it changes)
      if (!shouldBeSticky && navRef.current && navHeightRef.current === null) {
        navHeightRef.current = navRef.current.offsetHeight;
      }
      
      // Update active section based on scroll position
      // Use a larger offset so the active section changes before the header goes behind the nav
      const sectionElements = sections.map(s => ({
        id: s.id,
        element: document.getElementById(s.id),
      }));

      for (let i = sectionElements.length - 1; i >= 0; i--) {
        const { id, element } = sectionElements[i];
        if (element) {
          const rect = element.getBoundingClientRect();
          // Increase offset to trigger earlier - account for nav height (~70px) + buffer
          // This ensures the section becomes active before its header goes behind the nav
          const offset = shouldBeSticky ? 140 : 200;
          if (rect.top <= offset) {
            if (activeSection !== id) {
              onSectionChange(id);
            }
            break;
          }
        }
      }
      
      rafIdRef.current = null;
    };

    const handleScroll = () => {
      // Use requestAnimationFrame to batch updates and prevent excessive re-renders
      if (rafIdRef.current === null) {
        rafIdRef.current = requestAnimationFrame(updateStickyState);
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    updateStickyState(); // Check initial state
    
    // Recalculate threshold on resize
    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        stickyThresholdRef.current = rect.top + window.scrollY;
      }
    };
    window.addEventListener("resize", handleResize, { passive: true });
    
    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [activeSection, onSectionChange]);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      // Use a fixed offset that accounts for both sticky nav and header
      // Match the detection offset so scrolling positions the section correctly
      const offset = isSticky ? 140 : 200;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - offset;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth",
      });
      onSectionChange(sectionId);
    }
  };

  return (
    <div ref={containerRef}>
      {/* Placeholder to prevent layout shift when nav becomes sticky */}
      <div 
        ref={placeholderRef} 
        className="transition-all duration-300 ease-in-out" 
        style={{ 
          height: isSticky && navHeightRef.current ? `${navHeightRef.current}px` : '0px',
          overflow: 'hidden'
        }}
      />
      
      <nav
        ref={navRef}
        className={cn(
          "z-40",
          isSticky
            ? "fixed top-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-b shadow-sm"
            : "relative bg-transparent"
        )}
        style={{
          transition: isSticky ? 'background-color 0.3s ease-in-out, backdrop-filter 0.3s ease-in-out, box-shadow 0.3s ease-in-out' : 'none'
        }}
      >
        <div className="max-w-[1600px] mx-auto px-8 py-4">
          <div className="flex items-center justify-between gap-4">
            {/* Section Navigation Buttons */}
            <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide flex-1">
              {sections.map((section) => {
                const Icon = section.icon;
                const isActive = activeSection === section.id;
                return (
                  <button
                    key={section.id}
                    onClick={() => scrollToSection(section.id)}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 rounded-lg transition-all whitespace-nowrap",
                      isActive
                        ? "bg-indigo-500 text-white shadow-sm"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{section.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Time Filter Toggle */}
            <div className="inline-flex bg-white rounded-lg p-1.5 shadow-sm border border-gray-100 flex-shrink-0">
              <button
                onClick={() => onTimeFilterChange("today")}
                className={`px-5 py-2.5 rounded-md text-sm font-medium transition-all ${
                  timeFilter === "today"
                    ? "bg-indigo-500 text-white shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Today
              </button>
              <button
                onClick={() => onTimeFilterChange("weekly")}
                className={`px-5 py-2.5 rounded-md text-sm font-medium transition-all ${
                  timeFilter === "weekly"
                    ? "bg-indigo-500 text-white shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Weekly
              </button>
              <button
                onClick={() => onTimeFilterChange("monthly")}
                className={`px-5 py-2.5 rounded-md text-sm font-medium transition-all ${
                  timeFilter === "monthly"
                    ? "bg-indigo-500 text-white shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Monthly
              </button>
            </div>
          </div>
        </div>
      </nav>
    </div>
  );
}

