import { useCallback, useRef, useState } from "react";
import { Upload, Search } from "lucide-react";

interface Props {
  onUpload: (file: File) => void;
  isLoading?: boolean;
}

export function ImageUpload({ onUpload, isLoading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = useCallback((file: File | undefined) => {
    if (file && (file.type.startsWith("image/") || file.type.startsWith("video/"))) {
      setSelectedFile(file);
    }
  }, []);

  const handleAnalyze = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  return (
    <div className="bg-white border border-[#BAE8FF]/60 shadow-lg rounded-2xl p-6 flex flex-col h-full min-h-[400px]">
      <div className="flex items-center gap-2 mb-4">
        <Upload className="w-5 h-5 text-slate-500" />
        <h3 className="text-slate-800 font-bold text-sm">Upload Media</h3>
      </div>

      <div
        className={`flex-1 w-full border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-200
          ${dragOver ? "border-[#0096C7] bg-[#E0F7FF]/40" : "border-[#BAE8FF] bg-[#E0F7FF]/10 hover:border-[#0096C7]/50 hover:bg-[#E0F7FF]/20"}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFile(e.dataTransfer.files[0]);
        }}
      >
        <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center mb-4 shadow-sm border border-[#BAE8FF]">
          <Upload className="w-6 h-6 text-[#0096C7]" />
        </div>
        {selectedFile ? (
          <p className="text-slate-800 font-bold mb-1">{selectedFile.name}</p>
        ) : (
          <>
            <p className="text-slate-700 font-bold mb-1 text-sm">
              Drag & drop your file here
            </p>
            <p className="text-slate-400 text-xs mb-4">or click to browse your files</p>
          </>
        )}
        <div className="flex items-center gap-4 text-[11px] text-slate-500 font-semibold mt-auto pt-4">
          <span className="flex items-center gap-1"><span className="text-gray-500">📄</span> JPG, PNG, WEBP</span>
          <span className="flex items-center gap-1"><span className="text-gray-500">🎥</span> MP4, AVI</span>
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/*,video/*"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />

      <div className="mt-4">
        <button
          onClick={handleAnalyze}
          disabled={!selectedFile || isLoading}
          className="w-full py-3 rounded-xl bg-[#0096C7] hover:bg-[#007ea7] text-white text-sm font-bold flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_4px_12px_rgba(0,150,199,0.2)]"
        >
          <Search className="w-4 h-4" />
          {isLoading ? "Analyzing..." : "Analyze for Deepfake"}
        </button>
        <p className="text-center text-[11px] text-gray-500 mt-3">
          Max file size: 50 MB • Supported: Images & Videos
        </p>
      </div>
    </div>
  );
}
