import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Info } from "lucide-react";

interface SpeechSettingsProps {
  provider: "browser" | "elevenlabs";
  onProviderChange: (provider: "browser" | "elevenlabs") => void;
}

const SpeechSettings = ({ provider, onProviderChange }: SpeechSettingsProps) => {
  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-3">Voice Provider</h3>
      <RadioGroup value={provider} onValueChange={(val) => onProviderChange(val as "browser" | "elevenlabs")}>
        <div className="flex items-center space-x-2 mb-3">
          <RadioGroupItem value="browser" id="browser" />
          <Label htmlFor="browser" className="flex items-center gap-2 cursor-pointer">
            Browser Speech (Free)
            <Badge variant="secondary">Default</Badge>
          </Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="elevenlabs" id="elevenlabs" />
          <Label htmlFor="elevenlabs" className="flex items-center gap-2 cursor-pointer">
            ElevenLabs (Premium)
            <Badge variant="outline">Requires API Key</Badge>
          </Label>
        </div>
      </RadioGroup>

      {provider === "elevenlabs" && (
        <div className="mt-4 p-3 bg-muted/50 rounded-lg flex items-start gap-2">
          <Info className="w-4 h-4 mt-0.5 text-muted-foreground flex-shrink-0" />
          <div className="text-sm text-muted-foreground">
            <p className="font-medium mb-1">To use ElevenLabs:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Get your API key from elevenlabs.io</li>
              <li>Add it in Backend → Secrets → ELEVENLABS_API_KEY</li>
              <li>Create a Conversational AI agent in ElevenLabs dashboard</li>
              <li>Use your agent ID in conversations</li>
            </ol>
          </div>
        </div>
      )}
    </Card>
  );
};

export default SpeechSettings;
