import { useState } from "react";
import { Settings } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function FeedbackHeader() {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="mb-6 pb-4 border-b border-gray-200">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-1 h-8 bg-indigo-500 rounded-full"></div>
            <h1 className="text-2xl font-bold text-gray-900">At a Glance</h1>
          </div>
          <p className="text-gray-600 ml-4">Track your progress and improve your skills</p>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {/* Settings Button */}
          <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
            <DialogTrigger asChild>
              <button 
                className="p-2 rounded-lg bg-white border border-gray-100 shadow-sm hover:shadow-md transition-shadow"
                aria-label="Settings"
              >
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Progress Settings</DialogTitle>
                <DialogDescription>
                  Customize your progress view preferences
                </DialogDescription>
              </DialogHeader>
              <div className="py-4">
                <p className="text-sm text-gray-600">
                  Settings panel coming soon. Here you'll be able to customize which metrics to display and adjust your preferences.
                </p>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}

