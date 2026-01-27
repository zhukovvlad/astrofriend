import { motion, AnimatePresence } from "framer-motion";
import { Heart } from "lucide-react";
import { cn } from "@/lib/utils";

// Shared status emoji mapping to avoid duplication
const STATUS_EMOJI: Record<string, string> = {
  Bored: "😑",
  Annoyed: "😒",
  Distracted: "🙄",
  Neutral: "😐",
  Curious: "🤔",
  Intrigued: "😏",
  Interested: "😊",
  Amused: "😄",
  Flirty: "😘",
  Smitten: "😍",
  Obsessed: "🥵",
};

const getStatusEmoji = (statusLabel: string) =>
  STATUS_EMOJI[statusLabel] || "💭";

interface LoveMeterProps {
  score: number; // 0-100
  status: string; // e.g., "Intrigued", "Bored"
  scoreChange?: number; // Recent change for animation feedback
  variant?: "horizontal" | "vertical";
  showStatus?: boolean;
  className?: string;
}

/**
 * LoveMeter - Visual relationship score indicator
 * 
 * Displays the AI character's interest level with:
 * - Color gradient from cold (blue) to hot (red)
 * - Heartbeat animation that speeds up with higher scores
 * - Current emotional status display
 */
export function LoveMeter({
  score,
  status,
  scoreChange = 0,
  variant = "horizontal",
  showStatus = true,
  className,
}: LoveMeterProps) {
  // Clamp score between 0-100
  const clampedScore = Math.max(0, Math.min(100, score));
  
  // Calculate color based on score (blue -> purple -> pink -> red)
  const getScoreColor = (value: number) => {
    if (value < 20) return "from-blue-500 to-blue-400"; // Cold/Frozen
    if (value < 40) return "from-blue-400 to-purple-500"; // Cool
    if (value < 60) return "from-purple-500 to-pink-500"; // Neutral/Warming
    if (value < 80) return "from-pink-500 to-rose-500"; // Warm
    return "from-rose-500 to-red-500"; // Hot
  };
  
  // Get background color for the meter track
  const getTrackColor = (value: number) => {
    if (value < 20) return "bg-blue-950/30";
    if (value < 40) return "bg-purple-950/30";
    if (value < 60) return "bg-pink-950/30";
    return "bg-rose-950/30";
  };
  
  // Heartbeat animation speed based on score (faster = more interested)
  const heartbeatDuration = Math.max(0.3, 1.5 - (clampedScore / 100) * 1.2);

  const isVertical = variant === "vertical";
  
  return (
    <div
      className={cn(
        "flex items-center gap-3",
        isVertical && "flex-col-reverse",
        className
      )}
    >
      {/* Heartbeat Icon */}
      <motion.div
        className="relative"
        animate={{
          scale: [1, 1.2, 1, 1.1, 1],
        }}
        transition={{
          duration: heartbeatDuration,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        <Heart
          className={cn(
            "w-6 h-6 transition-colors duration-500",
            clampedScore < 20 && "text-blue-400",
            clampedScore >= 20 && clampedScore < 40 && "text-purple-400",
            clampedScore >= 40 && clampedScore < 60 && "text-pink-400",
            clampedScore >= 60 && clampedScore < 80 && "text-rose-400",
            clampedScore >= 80 && "text-red-400"
          )}
          fill={clampedScore >= 50 ? "currentColor" : "none"}
        />
        
        {/* Score change indicator */}
        <AnimatePresence>
          {scoreChange !== 0 && (
            <motion.span
              key={scoreChange}
              className={cn(
                "absolute -top-2 -right-2 text-xs font-bold",
                scoreChange > 0 ? "text-green-400" : "text-red-400"
              )}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              {scoreChange > 0 ? `+${scoreChange}` : scoreChange}
            </motion.span>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Progress Bar */}
      <div
        className={cn(
          "relative rounded-full overflow-hidden",
          getTrackColor(clampedScore),
          isVertical ? "w-3 h-24" : "h-3 flex-1 min-w-24"
        )}
      >
        <motion.div
          className={cn(
            "absolute rounded-full bg-linear-to-r",
            getScoreColor(clampedScore),
            isVertical ? "bottom-0 left-0 right-0" : "top-0 bottom-0 left-0"
          )}
          initial={false}
          animate={{
            [isVertical ? "height" : "width"]: `${clampedScore}%`,
          }}
          transition={{
            type: "spring",
            stiffness: 100,
            damping: 15,
          }}
        />
        
        {/* Pulse effect on the bar end */}
        <motion.div
          className={cn(
            "absolute rounded-full bg-white/30",
            isVertical ? "h-1 left-0 right-0" : "w-1 top-0 bottom-0"
          )}
          style={
            isVertical
              ? { bottom: `${clampedScore}%` }
              : { left: `${clampedScore}%` }
          }
          animate={{
            opacity: [0.3, 0.8, 0.3],
          }}
          transition={{
            duration: heartbeatDuration,
            repeat: Infinity,
          }}
        />
      </div>

      {/* Score Display */}
      <div
        className={cn(
          "flex items-center gap-1.5 text-sm font-medium",
          isVertical && "flex-col"
        )}
      >
        <span className="text-muted-foreground tabular-nums">
          {clampedScore}
        </span>
        
        {showStatus && (
          <span className="flex items-center gap-1">
            <span>{getStatusEmoji(status)}</span>
            <span className="text-xs text-muted-foreground hidden sm:inline">
              {status}
            </span>
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Compact version for chat header
 */
export function LoveMeterCompact({
  score,
  status,
  className,
}: {
  score: number;
  status: string;
  className?: string;
}) {
  const clampedScore = Math.max(0, Math.min(100, score));
  const heartbeatDuration = Math.max(0.3, 1.5 - (clampedScore / 100) * 1.2);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <motion.div
        animate={{ scale: [1, 1.15, 1] }}
        transition={{
          duration: heartbeatDuration,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        <Heart
          className={cn(
            "w-4 h-4",
            clampedScore < 20 && "text-blue-400",
            clampedScore >= 20 && clampedScore < 40 && "text-purple-400",
            clampedScore >= 40 && clampedScore < 60 && "text-pink-400",
            clampedScore >= 60 && clampedScore < 80 && "text-rose-400",
            clampedScore >= 80 && "text-red-400"
          )}
          fill={clampedScore >= 50 ? "currentColor" : "none"}
        />
      </motion.div>
      <span className="text-xs font-medium tabular-nums">{clampedScore}</span>
      <span className="text-sm">{getStatusEmoji(status)}</span>
    </div>
  );
}

export default LoveMeter;
