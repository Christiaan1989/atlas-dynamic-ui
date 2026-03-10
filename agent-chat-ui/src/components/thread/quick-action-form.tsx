"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  Car,
  FileText,
  Phone,
  ArrowRight,
  CalendarDays,
  MapPin,
  MessageSquareText,
  ChevronLeft,
  Sparkles,
  ImagePlus,
  XCircle,
} from "lucide-react";

type ActionType = "claim" | "damage" | "policy" | "upgrade" | null;

interface QuickActionFormProps {
  onSubmit: (message: string, files?: File[]) => void;
}

interface FormFields {
  date: string;
  location: string;
  description: string;
}

const ACTION_CONFIG: Record<
  Exclude<ActionType, null>,
  {
    icon: typeof Shield;
    title: string;
    subtitle: string;
    color: string;
    allowsPhoto: boolean;
    fields: {
      date: { label: string; placeholder: string; default: string };
      location: { label: string; placeholder: string; default: string };
      description: { label: string; placeholder: string; default: string };
    };
    buildMessage: (fields: FormFields) => string;
  }
> = {
  claim: {
    icon: Shield,
    title: "File a New Claim",
    subtitle: "We'll guide you through the process",
    color: "#C5961A",
    allowsPhoto: true,
    fields: {
      date: {
        label: "When did it happen?",
        placeholder: "e.g. Today, Yesterday, Feb 25",
        default: "Today",
      },
      location: {
        label: "Where did it happen?",
        placeholder: "e.g. Highway 101, Parking lot at Mall",
        default: "",
      },
      description: {
        label: "What happened?",
        placeholder: "e.g. I was rear-ended at a traffic light...",
        default: "",
      },
    },
    buildMessage: (f) => {
      const parts = ["I'd like to file a new insurance claim."];
      if (f.date) parts.push(`It happened ${f.date.toLowerCase()}.`);
      if (f.location) parts.push(`Location: ${f.location}.`);
      if (f.description) parts.push(f.description);
      if (!f.description)
        parts.push("I was involved in an accident and need to report it.");
      return parts.join(" ");
    },
  },
  damage: {
    icon: Car,
    title: "Damage Assessment",
    subtitle: "Upload photos for AI-powered analysis",
    color: "#C5961A",
    allowsPhoto: true,
    fields: {
      date: {
        label: "Damage location",
        placeholder: "e.g. Front bumper, Driver side door",
        default: "",
      },
      location: {
        label: "",
        placeholder: "",
        default: "",
      },
      description: {
        label: "",
        placeholder: "",
        default: "",
      },
    },
    buildMessage: (f) => {
      const parts = [
        "I need a damage assessment only - I'm not filing a claim yet.",
      ];
      if (f.date) parts.push(`The damage is on the ${f.date.toLowerCase()}.`);
      parts.push("I'll upload photos for analysis.");
      return parts.join(" ");
    },
  },
  policy: {
    icon: FileText,
    title: "Policy Questions",
    subtitle: "Get answers about your coverage",
    color: "#C5961A",
    allowsPhoto: false,
    fields: {
      date: {
        label: "Your question",
        placeholder: "e.g. What does my comprehensive coverage include?",
        default: "",
      },
      location: {
        label: "",
        placeholder: "",
        default: "",
      },
      description: {
        label: "",
        placeholder: "",
        default: "",
      },
    },
    buildMessage: (f) => {
      if (f.date) return `I have a question about my policy: ${f.date}`;
      return "I have a question about my insurance policy.";
    },
  },
  upgrade: {
    icon: Phone,
    title: "Coverage Upgrades",
    subtitle: "Explore better protection options",
    color: "#C5961A",
    allowsPhoto: false,
    fields: {
      date: {
        label: "Coverage type of interest",
        placeholder: "e.g. Comprehensive, Collision, Roadside assistance",
        default: "",
      },
      location: {
        label: "",
        placeholder: "",
        default: "",
      },
      description: {
        label: "",
        placeholder: "",
        default: "",
      },
    },
    buildMessage: (f) => {
      if (f.date)
        return `I'd like to explore ${f.date.toLowerCase()} coverage upgrade options for my policy.`;
      return "I'd like to see what coverage upgrade options are available for my policy.";
    },
  },
};

const ACTIONS: { type: Exclude<ActionType, null>; label: string; desc: string }[] = [
  { type: "claim", label: "File a new claim", desc: "Report an accident" },
  { type: "damage", label: "Damage assessment", desc: "Upload photos for AI analysis" },
  { type: "policy", label: "Policy questions", desc: "Coverage & exclusions" },
  { type: "upgrade", label: "Coverage upgrades", desc: "Explore better plans" },
];

export function QuickActionForm({ onSubmit }: QuickActionFormProps) {
  const [selectedAction, setSelectedAction] = useState<ActionType>(null);
  const [fields, setFields] = useState<FormFields>({
    date: "",
    location: "",
    description: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [photoPreviews, setPhotoPreviews] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSelectAction = (action: Exclude<ActionType, null>) => {
    const config = ACTION_CONFIG[action];
    setFields({
      date: config.fields.date.default,
      location: config.fields.location.default,
      description: config.fields.description.default,
    });
    setSelectedAction(action);
  };

  const handleBack = () => {
    setSelectedAction(null);
    setFields({ date: "", location: "", description: "" });
    setPhotoFiles([]);
    setPhotoPreviews([]);
  };

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setPhotoFiles((prev) => [...prev, ...files]);
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setPhotoPreviews((prev) => [...prev, ev.target?.result as string]);
      };
      reader.readAsDataURL(file);
    });
    // Reset the input so the same file can be re-selected
    e.target.value = "";
  };

  const removePhoto = (index: number) => {
    setPhotoFiles((prev) => prev.filter((_, i) => i !== index));
    setPhotoPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleFormSubmit = () => {
    if (!selectedAction) return;
    setIsSubmitting(true);
    const config = ACTION_CONFIG[selectedAction];
    const message = config.buildMessage(fields);

    // Brief delay for the submit animation
    setTimeout(() => {
      onSubmit(message, photoFiles.length > 0 ? photoFiles : undefined);
      setIsSubmitting(false);
      setSelectedAction(null);
      setFields({ date: "", location: "", description: "" });
      setPhotoFiles([]);
      setPhotoPreviews([]);
    }, 600);
  };

  const fieldIcons = [CalendarDays, MapPin, MessageSquareText];

  return (
    <div className="w-full max-w-lg">
      <AnimatePresence mode="wait">
        {!selectedAction ? (
          <motion.div
            key="buttons"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="grid grid-cols-2 gap-2.5"
          >
            {ACTIONS.map((action, i) => {
              const Icon = ACTION_CONFIG[action.type].icon;
              return (
                <motion.button
                  key={action.type}
                  type="button"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.3, ease: "easeOut" }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleSelectAction(action.type)}
                  className="group flex cursor-pointer items-center gap-2.5 rounded-xl border border-[#0F2B46]/10 bg-white/80 px-3 py-3 shadow-sm backdrop-blur-sm transition-colors hover:border-[#C5961A]/40 hover:bg-white"
                >
                  <div className="flex size-8 items-center justify-center rounded-lg bg-[#C5961A]/10 transition-colors group-hover:bg-[#C5961A]/20">
                    <Icon className="size-4 text-[#C5961A]" />
                  </div>
                  <div className="text-left">
                    <span className="text-xs font-medium text-[#0F2B46]">
                      {action.label}
                    </span>
                    <p className="text-[10px] leading-tight text-[#0F2B46]/50">
                      {action.desc}
                    </p>
                  </div>
                </motion.button>
              );
            })}
          </motion.div>
        ) : (
          <motion.div
            key="form"
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden rounded-2xl border border-[#0F2B46]/10 bg-white/90 shadow-lg backdrop-blur-sm"
          >
            {/* Form header */}
            <div className="flex items-center gap-3 border-b border-[#0F2B46]/5 bg-gradient-to-r from-[#0F2B46] to-[#1a3d5c] px-4 py-3">
              <motion.button
                type="button"
                whileHover={{ x: -2 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleBack}
                className="flex size-7 cursor-pointer items-center justify-center rounded-full bg-white/10 text-white/70 transition-colors hover:bg-white/20 hover:text-white"
              >
                <ChevronLeft className="size-4" />
              </motion.button>
              <div className="flex items-center gap-2">
                {(() => {
                  const Icon = ACTION_CONFIG[selectedAction].icon;
                  return (
                    <div className="flex size-7 items-center justify-center rounded-lg bg-[#C5961A]/20">
                      <Icon className="size-3.5 text-[#C5961A]" />
                    </div>
                  );
                })()}
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    {ACTION_CONFIG[selectedAction].title}
                  </h3>
                  <p className="text-[10px] text-white/50">
                    {ACTION_CONFIG[selectedAction].subtitle}
                  </p>
                </div>
              </div>
            </div>

            {/* Form fields */}
            <div className="space-y-3 p-4">
              {(["date", "location", "description"] as const)
                .filter((fieldKey) => {
                  const config = ACTION_CONFIG[selectedAction].fields[fieldKey];
                  return config.label !== "";
                })
                .map((fieldKey, i) => {
                  const config = ACTION_CONFIG[selectedAction].fields[fieldKey];
                  const FieldIcon = fieldIcons[i];
                  return (
                    <motion.div
                      key={fieldKey}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{
                        delay: 0.1 + i * 0.08,
                        duration: 0.35,
                        ease: "easeOut",
                      }}
                    >
                      <label className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#0F2B46]/40">
                        <FieldIcon className="size-3" />
                        {config.label}
                      </label>
                      {fieldKey === "description" ? (
                        <textarea
                          value={fields[fieldKey]}
                          onChange={(e) =>
                            setFields((prev) => ({
                              ...prev,
                              [fieldKey]: e.target.value,
                            }))
                          }
                          placeholder={config.placeholder}
                          rows={2}
                          className="w-full resize-none rounded-lg border border-[#0F2B46]/10 bg-[#0F2B46]/[0.02] px-3 py-2 text-xs text-[#0F2B46] transition-colors placeholder:text-[#0F2B46]/25 focus:border-[#C5961A]/40 focus:outline-none"
                        />
                      ) : (
                        <input
                          type="text"
                          value={fields[fieldKey]}
                          onChange={(e) =>
                            setFields((prev) => ({
                              ...prev,
                              [fieldKey]: e.target.value,
                            }))
                          }
                          placeholder={config.placeholder}
                          className="w-full rounded-lg border border-[#0F2B46]/10 bg-[#0F2B46]/[0.02] px-3 py-2 text-xs text-[#0F2B46] transition-colors placeholder:text-[#0F2B46]/25 focus:border-[#C5961A]/40 focus:outline-none"
                        />
                      )}
                    </motion.div>
                  );
                })}
            </div>

            {/* Photo upload section — only for claim & damage */}
            {selectedAction && ACTION_CONFIG[selectedAction].allowsPhoto && (
              <div className="border-t border-[#0F2B46]/5 px-4 py-3">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.35, duration: 0.3 }}
                >
                  <label className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#0F2B46]/40">
                    <ImagePlus className="size-3" />
                    Photos (optional)
                  </label>
                  <div className="flex flex-wrap items-center gap-2">
                    {photoPreviews.map((src, i) => (
                      <div key={i} className="group relative">
                        <img
                          src={src}
                          alt={`Upload ${i + 1}`}
                          className="size-14 rounded-lg border border-[#0F2B46]/10 object-cover"
                        />
                        <button
                          type="button"
                          onClick={() => removePhoto(i)}
                          className="absolute -top-1.5 -right-1.5 cursor-pointer rounded-full bg-white shadow-sm opacity-0 transition-opacity group-hover:opacity-100"
                        >
                          <XCircle className="size-4 text-red-400" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="flex size-14 cursor-pointer flex-col items-center justify-center gap-0.5 rounded-lg border border-dashed border-[#0F2B46]/15 bg-[#0F2B46]/[0.02] text-[#0F2B46]/30 transition-colors hover:border-[#C5961A]/40 hover:text-[#C5961A]/60"
                    >
                      <ImagePlus className="size-4" />
                      <span className="text-[8px] font-medium">Add</span>
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/gif,image/webp"
                      multiple
                      onChange={handlePhotoSelect}
                      className="hidden"
                    />
                  </div>
                </motion.div>
              </div>
            )}

            {/* Submit button */}
            <div className="border-t border-[#0F2B46]/5 px-4 py-3">
              <motion.button
                type="button"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleFormSubmit}
                disabled={isSubmitting}
                className="group flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#0F2B46] to-[#1a3d5c] px-4 py-2.5 text-sm font-medium text-white shadow-md transition-all hover:shadow-lg disabled:opacity-70"
              >
                <AnimatePresence mode="wait">
                  {isSubmitting ? (
                    <motion.div
                      key="submitting"
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.5 }}
                      className="flex items-center gap-2"
                    >
                      <Sparkles className="size-4 animate-pulse text-[#C5961A]" />
                      <span>Starting conversation...</span>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="ready"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      <span>Start Conversation</span>
                      <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
