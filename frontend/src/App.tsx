import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import {
  UploadCloud,
  FolderOpen,
  Image as ImageIcon,
  CheckCircle2,
  Circle,
  Loader2,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  X,
  ZoomIn,
  ZoomOut,
  Pencil,
  Trash2,
  Download,
  FileText,
  Wifi,
  WifiOff,
  Sun,
  Moon,
  Sparkles,
  Layers,
  ScanSearch,
  Eraser,
  Copy,
  AlertTriangle,
  CheckSquare,
  Square,
  RefreshCw,
} from "lucide-react";

const API_BASE = "http://localhost:8000";

const PIPELINE_STAGES = [
  { key: "features", label: "Extracting Features", icon: Layers },
  { key: "duplicates", label: "Removing Duplicates", icon: Copy },
  { key: "clustering", label: "Clustering Images", icon: Sparkles },
  { key: "ocr", label: "OCR Naming", icon: ScanSearch },
  { key: "background", label: "Removing Backgrounds", icon: Eraser },
];

const SUPPORTED_TYPES = ["JPG", "PNG", "WEBP", "HEIC"];

function formatBytes(bytes: number) {
  if (!bytes) return "0 MB";
  const mb = bytes / (1024 * 1024);
  if (mb < 1024) return `${mb.toFixed(1)} MB`;
  return `${(mb / 1024).toFixed(2)} GB`;
}

function formatElapsed(seconds: number) {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
}

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function NotificationStack({ notifications, onDismiss }: any) {
  return (
    <div className="notif-stack">
      {notifications.map((n: any) => (
        <div key={n.id} className={`notif notif-${n.type}`}>
          {n.type === "error" ? (
            <AlertTriangle size={16} />
          ) : (
            <CheckCircle2 size={16} />
          )}
          <span>{n.message}</span>
          <button
            className="notif-close"
            onClick={() => onDismiss(n.id)}
            aria-label="Dismiss notification"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

function TopNav({ theme, onToggleTheme, connectionStatus, onStartOver }: any) {
  return (
    <header className="topnav">
      <div className="topnav-left">
        <div className="brand-block">
          <span className="brand-name">Sortline</span>
        </div>
        {onStartOver && (
          <button className="btn-ghost small" onClick={onStartOver} style={{marginLeft: '12px'}}>
            <RefreshCw size={14} /> Start Over
          </button>
        )}
      </div>
      <div className="topnav-right">
        <div className={`conn-pill conn-${connectionStatus}`}>
          {connectionStatus === "connected" ? (
            <Wifi size={14} />
          ) : (
            <WifiOff size={14} />
          )}
          <span>
            {connectionStatus === "connected" ? "Live" : "Offline"}
          </span>
        </div>
      </div>
    </header>
  );
}

function UploadZone({ onFilesAdded, uploadedFiles, onClear, onStart, isOffline }: any) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const totalSize = useMemo(
    () => uploadedFiles.reduce((sum: number, f: any) => sum + (f.size || 0), 0),
    [uploadedFiles]
  );

  const handleDrop = (e: any) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files || []);
    if (files.length) onFilesAdded(files);
  };

  return (
    <section className="upload-section">
      <div className="hero-copy">
        <h1>Turn a messy product folder into a clean catalog.</h1>
        <p>
          Drop in your raw shoot. Sortline extracts features, drops
          duplicates, clusters look-alikes, names them from on-image text,
          and strips the backgrounds — automatically.
        </p>
      </div>

      <div
        className={`upload-zone ${dragOver ? "drag-over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          {...{ webkitdirectory: "true", directory: "true" } as any}
          onChange={(e) => onFilesAdded(Array.from(e.target.files || []))}
        />
        <div className="upload-icon-wrap">
          <UploadCloud size={30} />
        </div>
        <p className="upload-title">Drag a folder of product photos here</p>
        <p className="upload-sub">or</p>
        <button className="btn-secondary" onClick={() => inputRef.current?.click()}>
          <FolderOpen size={15} />
          Browse folder
        </button>
        <div className="supported-types">
          {SUPPORTED_TYPES.map((t) => (
            <span key={t} className="type-chip">
              {t}
            </span>
          ))}
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="upload-stats">
          <div className="stat-block">
            <span className="stat-value">{uploadedFiles.length}</span>
            <span className="stat-label">images queued</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-block">
            <span className="stat-value">{formatBytes(totalSize)}</span>
            <span className="stat-label">total size</span>
          </div>
          <div className="upload-actions">
            <button className="btn-ghost" onClick={onClear}>
              Clear
            </button>
            <button className="btn-primary" onClick={onStart} disabled={isOffline}>
              <Sparkles size={15} />
              Start processing
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function StageTimeline({ stages, currentStageKey, completedKeys }: any) {
  return (
    <ol className="stage-timeline">
      {stages.map((stage: any) => {
        const done = completedKeys.includes(stage.key);
        const active = stage.key === currentStageKey;
        const Icon = stage.icon;
        return (
          <li
            key={stage.key}
            className={`stage-row ${done ? "done" : ""} ${
              active ? "active" : ""
            }`}
          >
            <span className="stage-marker">
              {done ? (
                <CheckCircle2 size={16} />
              ) : active ? (
                <Loader2 size={16} className="spin" />
              ) : (
                <Circle size={16} />
              )}
            </span>
            <Icon size={14} className="stage-icon" />
            <span className="stage-label">{stage.label}</span>
          </li>
        );
      })}
    </ol>
  );
}

function ProcessingPanel({
  progress,
  progressMsg,
  currentStageKey,
  completedKeys,
  elapsed,
  processedCount,
  totalCount,
}: any) {
  let eta = "";
  if (progress > 0 && progress < 100) {
    const totalEst = elapsed / (progress / 100);
    const remaining = Math.max(0, totalEst - elapsed);
    eta = remaining > 0 ? `~${formatElapsed(remaining)} remaining` : "Almost done...";
  }

  return (
    <section className="processing-panel">
      <div className="panel-header">
        <h2>Processing your catalog</h2>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
          <span className="panel-elapsed">{formatElapsed(elapsed)} elapsed</span>
          {eta && <span className="panel-elapsed" style={{ color: 'var(--primary)', fontWeight: 600 }}>{eta}</span>}
        </div>
      </div>
      <p style={{marginTop: '-10px', marginBottom: '20px', color: 'var(--muted)', fontSize: '14px'}}>{progressMsg}</p>

      <div className="progress-track">
        <div
          className="progress-fill"
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
      <div className="progress-meta">
        <span>{Math.round(progress)}%</span>
        <span>
          {processedCount} / {totalCount} images
        </span>
      </div>

      <StageTimeline
        stages={PIPELINE_STAGES}
        currentStageKey={currentStageKey}
        completedKeys={completedKeys}
      />
    </section>
  );
}

function Thumb({ image, onClick, selected, onToggleSelect, onDelete }: any) {
  const imgSrc = image.bgRemoved ? image.url : image.orig_url;
  return (
    <div className="thumb-cell">
      <button className="thumb-frame" onClick={onClick} title={image.filename}>
        <div className={`thumb-art ${image.bgRemoved ? "bg-removed" : ""}`} aria-hidden="true">
          {imgSrc ? <img src={imgSrc} style={{width: '100%', height: '100%', objectFit: 'contain'}} alt="" /> : <ImageIcon size={22} />}
        </div>
        {image.bgRemoved && <span className="thumb-tag">no-bg</span>}
      </button>
      <div className="thumb-controls">
        <button
          className="thumb-select"
          onClick={(e) => {
            e.stopPropagation();
            onToggleSelect(image.id);
          }}
          aria-label={selected ? "Deselect image" : "Select image"}
        >
          {selected ? <CheckSquare size={14} /> : <Square size={14} />}
        </button>
        <button
          className="thumb-delete"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(image.id);
          }}
          aria-label="Delete image"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  );
}

function GroupCard({
  group,
  expanded,
  onToggleExpand,
  onRename,
  onToggleReview,
  onOpenImage,
  onToggleImageSelect,
  onDeleteImage,
}: any) {
  const [editing, setEditing] = useState(false);
  const [draftName, setDraftName] = useState(group.name);

  const selectedCount = group.images.filter((i: any) => i.selected).length;

  const commitRename = () => {
    setEditing(false);
    const trimmed = draftName.trim();
    if (trimmed && trimmed !== group.name) onRename(group.id, trimmed);
    else setDraftName(group.name);
  };

  return (
    <article className={`group-card ${expanded ? "expanded" : ""}`}>
      <div className="group-card-top">
        <button
          className="group-thumb-preview"
          onClick={() => onToggleExpand(group.id)}
          aria-label="Toggle group"
          style={{overflow: 'hidden'}}
        >
          {group.images.length > 0 ? (
            <img src={group.images[0].url} style={{width: '100%', height: '100%', objectFit: 'cover'}} alt="" />
          ) : <Layers size={18} />}
        </button>

        <div className="group-info">
          {editing ? (
            <input
              className="group-name-input"
              value={draftName}
              autoFocus
              onChange={(e) => setDraftName(e.target.value)}
              onBlur={commitRename}
              onKeyDown={(e) => {
                if (e.key === "Enter") commitRename();
                if (e.key === "Escape") {
                  setDraftName(group.name);
                  setEditing(false);
                }
              }}
            />
          ) : (
            <div className="group-name-row">
              <h3>{group.name}</h3>
              <button
                className="icon-btn subtle"
                onClick={() => setEditing(true)}
                aria-label="Rename group"
              >
                <Pencil size={13} />
              </button>
            </div>
          )}
          <div className="group-meta-row">
            <span>{group.images.length} images</span>
            {group.confidence && (
              <span className="confidence-chip">
                {Math.round(group.confidence * 100)}% match
              </span>
            )}
            {group.reviewed && (
              <span className="reviewed-badge">
                <CheckCircle2 size={12} /> Reviewed
              </span>
            )}
            <span className="selected-count">{selectedCount} selected</span>
          </div>
        </div>

        <div className="group-card-actions">
          <button
            className={`btn-ghost small ${group.reviewed ? "active" : ""}`}
            onClick={() => onToggleReview(group.id)}
          >
            {group.reviewed ? "Reviewed" : "Mark reviewed"}
          </button>
          <button
            className="icon-btn"
            onClick={() => onToggleExpand(group.id)}
            aria-label="Expand group"
          >
            {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="group-card-body">
          <div className="thumb-grid">
            {group.images.map((img: any) => (
              <Thumb
                key={img.id}
                image={img}
                selected={img.selected}
                onClick={() => onOpenImage(group.id, img.id)}
                onToggleSelect={(imgId: any) => onToggleImageSelect(group.id, imgId)}
                onDelete={(imgId: any) => onDeleteImage(group.id, imgId)}
              />
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

function ImageModal({ group, imageIndex, onClose, onNav, onToggleBg }: any) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragState = useRef<any>(null);

  const image = group.images[imageIndex];

  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [imageIndex]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") onNav(1);
      if (e.key === "ArrowLeft") onNav(-1);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose, onNav]);

  if (!image) return null;

  const startDrag = (e: any) => {
    dragState.current = { x: e.clientX, y: e.clientY, pan };
  };
  const onDrag = (e: any) => {
    if (!dragState.current) return;
    const dx = e.clientX - dragState.current.x;
    const dy = e.clientY - dragState.current.y;
    setPan({ x: dragState.current.pan.x + dx, y: dragState.current.pan.y + dy });
  };
  const endDrag = () => {
    dragState.current = null;
  };

  const imgSrc = image.bgRemoved ? image.url : image.orig_url;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-shell" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close">
          <X size={18} />
        </button>

        <button
          className="modal-nav modal-nav-left"
          onClick={() => onNav(-1)}
          aria-label="Previous image"
        >
          <ChevronLeft size={22} />
        </button>

        <div
          className="modal-canvas"
          onMouseDown={startDrag}
          onMouseMove={onDrag}
          onMouseUp={endDrag}
          onMouseLeave={endDrag}
        >
          <div
            className={`modal-art ${image.bgRemoved ? "bg-removed" : ""}`}
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            }}
          >
            {imgSrc ? <img src={imgSrc} style={{maxWidth: '100%', maxHeight: '100%', objectFit: 'contain'}} alt="" /> : <ImageIcon size={64} />}
          </div>
        </div>

        <button
          className="modal-nav modal-nav-right"
          onClick={() => onNav(1)}
          aria-label="Next image"
        >
          <ChevronRight size={22} />
        </button>

        <div className="modal-toolbar">
          <button className="icon-btn" onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}>
            <ZoomOut size={15} />
          </button>
          <span className="zoom-value">{Math.round(zoom * 100)}%</span>
          <button className="icon-btn" onClick={() => setZoom((z) => Math.min(3, z + 0.25))}>
            <ZoomIn size={15} />
          </button>
          <span className="toolbar-divider" />
          <button
            className={`btn-ghost small ${image.bgRemoved ? "active" : ""}`}
            onClick={() => onToggleBg(group.id, image.id)}
          >
            {image.bgRemoved ? "Original" : "Background removed"}
          </button>
        </div>

        <div className="modal-meta">
          <span>{image.filename}</span>
          <span>
            {imageIndex + 1} / {group.images.length}
          </span>
        </div>
      </div>
    </div>
  );
}

function EmptyResults() {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <Layers size={26} />
      </div>
      <h3>No groups yet</h3>
      <p>Upload a folder and run processing to see clustered products here.</p>
    </div>
  );
}

function ExportFooter({ groups, onExport, exporting }: any) {
  const totalGroups = groups.length;
  const selectedImages = groups.reduce(
    (sum: number, g: any) => sum + g.images.filter((i: any) => i.selected).length,
    0
  );

  return (
    <footer className="export-footer">
      <div className="export-stats">
        <div className="export-stat">
          <span className="export-stat-value">{totalGroups}</span>
          <span className="export-stat-label">groups</span>
        </div>
        <div className="export-stat">
          <span className="export-stat-value">{selectedImages}</span>
          <span className="export-stat-label">images selected</span>
        </div>
      </div>
      <div className="export-actions">
        <button
          className="btn-primary"
          onClick={onExport}
          disabled={exporting || selectedImages === 0}
        >
          {exporting ? (
            <Loader2 size={15} className="spin" />
          ) : (
            <Download size={15} />
          )}
          {exporting ? "Exporting…" : "Export final images"}
        </button>
      </div>
    </footer>
  );
}

export default function App() {
  const [theme, setTheme] = useState("light");
  const [connectionStatus, setConnectionStatus] = useState("disconnected");

  useEffect(() => {
    let mounted = true;
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/health`);
        if (res.ok && mounted) {
          setConnectionStatus("connected");
        } else if (mounted) {
          setConnectionStatus("disconnected");
        }
      } catch (err) {
        if (mounted) setConnectionStatus("disconnected");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 3000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState("");
  const [currentStageKey, setCurrentStageKey] = useState<string | null>(null);
  const [completedKeys, setCompletedKeys] = useState<string[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [processedCount, setProcessedCount] = useState(0);

  const [groups, setGroups] = useState<any[]>([]);
  const [expandedGroupId, setExpandedGroupId] = useState<string | null>(null);
  const [modalState, setModalState] = useState<any>(null);
  const [exporting, setExporting] = useState(false);

  const [notifications, setNotifications] = useState<any[]>([]);
  const timerRef = useRef<any>(null);
  const sseRef = useRef<any>(null);
  const simRef = useRef<any>(null);

  const pushNotification = useCallback((message: string, type = "success") => {
    const id = uid();
    setNotifications((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 4000);
  }, []);

  const dismissNotification = (id: string) =>
    setNotifications((prev) => prev.filter((n) => n.id !== id));

  const handleFilesAdded = (files: File[]) => {
    const imageFiles = files.filter((f) => f.type.startsWith("image/"));
    if (imageFiles.length === 0) {
      pushNotification("No supported image files found in that selection.", "error");
      return;
    }
    setUploadedFiles((prev) => [...prev, ...imageFiles]);
  };

  const clearUpload = () => {
    stopAllTimers();
    setUploadedFiles([]);
    setProcessing(false);
    setGroups([]);
    setCompletedKeys([]);
    setCurrentStageKey(null);
    setProgress(0);
    setProgressMsg("");
    setExpandedGroupId(null);
    setModalState(null);
    localStorage.removeItem("sortline_job_id");
  };

  const stopAllTimers = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (simRef.current) clearInterval(simRef.current);
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
  };

  const finishProcessing = useCallback(() => {
    stopAllTimers();
    setProcessing(false);
    setProgress(100);
    setCompletedKeys(PIPELINE_STAGES.map((s) => s.key));
    pushNotification("Processing complete — groups are ready to review.");
    
    // Trigger system notification if permitted
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("Sortline", {
        body: "Processing complete — your groups are ready to review!",
      });
    }
  }, []);

  const connectSSE = useCallback((jobId: string, totalImages: number) => {
    try {
      const es = new EventSource(`${API_BASE}/api/events/${jobId}`);
      sseRef.current = es;

      es.onopen = () => setConnectionStatus("connected");

      es.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === 'progress') {
            setProgressMsg(msg.data);
            
            const pText = msg.data.toLowerCase();
            let newKeys = [...completedKeys];
            if (pText.includes("extract")) {
              setCurrentStageKey("features");
              setProgress(20);
            } else if (pText.includes("duplicate")) {
              setCurrentStageKey("duplicates");
              if (!newKeys.includes("features")) newKeys.push("features");
              setProgress(40);
            } else if (pText.includes("group") || pText.includes("cluster")) {
              setCurrentStageKey("clustering");
              if (!newKeys.includes("duplicates")) newKeys.push("duplicates");
              setProgress(60);
            } else if (pText.includes("ocr")) {
              setCurrentStageKey("ocr");
              if (!newKeys.includes("clustering")) newKeys.push("clustering");
              setProgress(80);
            } else if (pText.includes("bg") || pText.includes("background")) {
              setCurrentStageKey("background");
              if (!newKeys.includes("ocr")) newKeys.push("ocr");
              setProgress(90);
            }
            setCompletedKeys(newKeys);
            
          } else if (msg.event === 'group') {
            const newGroup = {
              id: msg.data.id,
              name: msg.data.name,
              job_id: jobId,
              reviewed: false,
              images: msg.data.images.map((img: any) => ({
                id: uid(),
                filename: img.original,
                bg_removed_filename: img.bg_removed,
                selected: true,
                bgRemoved: true,
                url: `${API_BASE}/images/${jobId}/${img.bg_removed}`,
                orig_url: `${API_BASE}/images/${jobId}/${img.original}`
              }))
            };
            setGroups((prev) => [...prev, newGroup]);
          } else if (msg.event === 'done') {
             finishProcessing();
          } else if (msg.event === 'error') {
             pushNotification(`Error: ${msg.data}`, "error");
             finishProcessing();
          }
        } catch {
        }
      };

      es.onerror = () => {
        es.close();
        sseRef.current = null;
        setConnectionStatus("disconnected");
      };
    } catch (err) {
      setConnectionStatus("disconnected");
    }
  }, [completedKeys]);

  useEffect(() => {
    const savedJobId = localStorage.getItem("sortline_job_id");
    if (!savedJobId) return;

    const restoreJob = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${savedJobId}`);
        if (!res.ok) {
           localStorage.removeItem("sortline_job_id");
           return;
        }
        const data = await res.json();
        if (data.error) {
           localStorage.removeItem("sortline_job_id");
           return;
        }

        setProgressMsg(data.progress_msg || "");
        
        // Restore groups
        const restoredGroups = data.groups.map((g: any) => ({
          id: g.id,
          name: g.name,
          job_id: data.id,
          reviewed: false,
          images: g.images.map((img: any) => ({
            id: uid(),
            filename: img.original,
            bg_removed_filename: img.bg_removed,
            selected: true,
            bgRemoved: true,
            url: `${API_BASE}/images/${data.id}/${img.bg_removed}`,
            orig_url: `${API_BASE}/images/${data.id}/${img.original}`
          }))
        }));
        setGroups(restoredGroups);

        if (data.status === "processing") {
          setProcessing(true);
          connectSSE(data.id, 0); 
        } else if (data.status === "done") {
          setProcessing(false);
          setCompletedKeys(PIPELINE_STAGES.map((s) => s.key));
          setProgress(100);
        }
      } catch (e) {
        console.error(e);
      }
    };
    restoreJob();
  }, [connectSSE]);

  const startProcessing = async () => {
    if (uploadedFiles.length === 0) return;
    
    // Request notification permission if we haven't asked yet
    if ("Notification" in window && Notification.permission !== "denied" && Notification.permission !== "granted") {
      Notification.requestPermission();
    }
    
    setProcessing(true);
    setProgress(0);
    setProgressMsg("Starting...");
    setElapsed(0);
    setProcessedCount(0);
    setCompletedKeys([]);
    setCurrentStageKey(PIPELINE_STAGES[0].key);
    setGroups([]);

    timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);

    try {
      const formData = new FormData();
      uploadedFiles.forEach((f) => formData.append("files", f));
      const res = await fetch(`${API_BASE}/api/process`, { method: "POST", body: formData });
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      const data = await res.json();
      localStorage.setItem("sortline_job_id", data.job_id);
      connectSSE(data.job_id, uploadedFiles.length);
    } catch (err: any) {
      pushNotification(`Processing failed: ${err.message}`, "error");
      stopAllTimers();
      setProcessing(false);
    }
  };

  useEffect(() => stopAllTimers, []);

  const toggleExpandGroup = (groupId: string) =>
    setExpandedGroupId((prev) => (prev === groupId ? null : groupId));

  const renameGroup = async (groupId: string, newName: string) => {
    setGroups((prev) =>
      prev.map((g) => (g.id === groupId ? { ...g, name: newName } : g))
    );
  };

  const toggleReviewGroup = async (groupId: string) => {
    setGroups((prev) =>
      prev.map((g) => {
        if (g.id !== groupId) return g;
        return { ...g, reviewed: !g.reviewed };
      })
    );
  };

  const toggleImageSelect = (groupId: string, imageId: string) => {
    setGroups((prev) =>
      prev.map((g) =>
        g.id !== groupId
          ? g
          : {
              ...g,
              images: g.images.map((img: any) =>
                img.id === imageId ? { ...img, selected: !img.selected } : img
              ),
            }
      )
    );
  };

  const deleteImage = (groupId: string, imageId: string) => {
    setGroups((prev) =>
      prev.map((g) =>
        g.id !== groupId
          ? g
          : { ...g, images: g.images.filter((img: any) => img.id !== imageId) }
      )
    );
    pushNotification("Image removed from group.");
  };

  const toggleImageBg = (groupId: string, imageId: string) => {
    setGroups((prev) =>
      prev.map((g) =>
        g.id !== groupId
          ? g
          : {
              ...g,
              images: g.images.map((img: any) =>
                img.id === imageId ? { ...img, bgRemoved: !img.bgRemoved } : img
              ),
            }
      )
    );
  };

  const openImage = (groupId: string, imageId: string) => {
    const group = groups.find((g) => g.id === groupId);
    const index = group?.images.findIndex((img: any) => img.id === imageId) ?? 0;
    setModalState({ groupId, imageIndex: index });
  };

  const navModal = (delta: number) => {
    setModalState((prev: any) => {
      if (!prev) return prev;
      const group = groups.find((g) => g.id === prev.groupId);
      if (!group) return prev;
      const nextIndex =
        (prev.imageIndex + delta + group.images.length) % group.images.length;
      return { ...prev, imageIndex: nextIndex };
    });
  };

  const activeModalGroup = modalState
    ? groups.find((g) => g.id === modalState.groupId)
    : null;

  const handleExport = async () => {
    setExporting(true);
    try {
      const exportGroups = groups.map(g => ({
        id: g.id,
        name: g.name,
        job_id: g.job_id, 
        images: g.images.filter((img: any) => img.selected).map((img: any) => ({
          use_bg_removed: img.bgRemoved,
          original: img.filename,
          bg_removed: img.bg_removed_filename
        }))
      }));
      const res = await fetch(`${API_BASE}/api/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ groups: exportGroups })
      });
      const data = await res.json();
      window.location.href = `${API_BASE}${data.download_url}`;
      pushNotification("Export ready — check your downloads.");
    } catch {
      pushNotification("Export failed", "error");
    } finally {
      setExporting(false);
    }
  };

  const hasGroups = groups.length > 0;
  const showUpload = !processing && !hasGroups;

  return (
    <div className={`app-shell theme-${theme}`}>
      <style>{styles}</style>

      <TopNav
        theme={theme}
        onToggleTheme={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
        connectionStatus={connectionStatus}
        onStartOver={(!showUpload || processing) ? clearUpload : undefined}
      />

      <NotificationStack notifications={notifications} onDismiss={dismissNotification} />

      <main className="app-main">
        {showUpload && (
          <UploadZone
            onFilesAdded={handleFilesAdded}
            uploadedFiles={uploadedFiles}
            onClear={clearUpload}
            onStart={startProcessing}
            isOffline={connectionStatus === "disconnected"}
          />
        )}

        {processing && (
          <ProcessingPanel
            progress={progress}
            progressMsg={progressMsg}
            currentStageKey={currentStageKey}
            completedKeys={completedKeys}
            elapsed={elapsed}
            processedCount={processedCount}
            totalCount={uploadedFiles.length}
          />
        )}

        {!processing && (
          <section className="results-section">
            <div className="results-header">
              <h2>Discovered groups</h2>
            </div>

            {hasGroups ? (
              <div className="group-list">
                {groups.map((group) => (
                  <GroupCard
                    key={group.id}
                    group={group}
                    expanded={expandedGroupId === group.id}
                    onToggleExpand={toggleExpandGroup}
                    onRename={renameGroup}
                    onToggleReview={toggleReviewGroup}
                    onOpenImage={openImage}
                    onToggleImageSelect={toggleImageSelect}
                    onDeleteImage={deleteImage}
                  />
                ))}
              </div>
            ) : (
              !showUpload && <EmptyResults />
            )}
          </section>
        )}
      </main>

      {hasGroups && !processing && (
        <ExportFooter
          groups={groups}
          onExport={handleExport}
          exporting={exporting}
        />
      )}

      {modalState && activeModalGroup && (
        <ImageModal
          group={activeModalGroup}
          imageIndex={modalState.imageIndex}
          onClose={() => setModalState(null)}
          onNav={navModal}
          onToggleBg={toggleImageBg}
        />
      )}
    </div>
  );
}

const styles = `
  .app-shell {
    --bg: #f7f2e9; 
    --card: #fffdf9; 
    --primary: #4aa87a; 
    --accent: #3a8f66; 
    --text: #463f37; 
    --muted: #6f6558; 
    --success: #4aa87a; 
    --warning: #e6b45c; 
    --error: #e8896a; 
    --border: #ece2d4;
    font-family: 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  .app-shell.theme-dark {
    --bg: #1E1B17;
    --card: #29241F;
    --text: #F3EFE8;
    --muted: #A69C8D;
    --border: rgba(255,255,255,0.08);
  }
  .app-shell * { box-sizing: border-box; }
  button { font-family: inherit; cursor: pointer; }

  /* Top nav */
  .topnav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 28px; border-bottom: 1px solid var(--border);
    background: var(--card); position: sticky; top: 0; z-index: 20;
  }
  .topnav-left { display: flex; align-items: center; gap: 10px; }
  .logo-mark {
    width: 34px; height: 34px; border-radius: 10px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    display: flex; align-items: center; justify-content: center; color: white;
  }
  .brand-block { display: flex; flex-direction: column; line-height: 1.15; }
  .brand-name { font-weight: 700; font-size: 15px; font-family: 'Playfair Display', serif; }
  .brand-sub { font-size: 11px; color: var(--muted); }
  .topnav-right { display: flex; align-items: center; gap: 10px; }
  .conn-pill {
    display: flex; align-items: center; gap: 6px; font-size: 12px;
    padding: 5px 10px; border-radius: 999px; background: rgba(76,175,80,0.1);
    color: var(--success);
  }
  .conn-pill.conn-disconnected { background: rgba(229,57,53,0.08); color: var(--error); }
  .icon-btn {
    border: 1px solid var(--border); background: transparent; color: var(--text);
    width: 32px; height: 32px; border-radius: 8px; display: flex;
    align-items: center; justify-content: center; transition: all .15s ease;
  }
  .icon-btn:hover { background: var(--accent); color: white; border-color: transparent; }
  .icon-btn.subtle { border: none; width: 24px; height: 24px; }

  /* Notifications */
  .notif-stack { position: fixed; top: 70px; right: 20px; z-index: 50; display: flex; flex-direction: column; gap: 8px; }
  .notif {
    display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 10px;
    background: var(--card); box-shadow: 0 8px 24px rgba(0,0,0,0.12); font-size: 13px;
    min-width: 240px; animation: slideIn .2s ease;
  }
  .notif-success { border-left: 3px solid var(--success); }
  .notif-error { border-left: 3px solid var(--error); }
  .notif-close { margin-left: auto; background: none; border: none; color: var(--muted); }
  @keyframes slideIn { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }

  .app-main { flex: 1; max-width: 1200px; width: 100%; margin: 0 auto; padding: 40px 24px 100px; }

  /* Upload */
  .hero-copy { text-align: center; max-width: 640px; margin: 0 auto 32px; }
  .hero-copy h1 { font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; margin: 0 0 12px; letter-spacing: -0.01em; }
  .hero-copy p { color: var(--muted); font-size: 15px; line-height: 1.6; margin: 0; }

  .upload-zone {
    border: 2px dashed var(--border); border-radius: 20px; padding: 48px 24px;
    display: flex; flex-direction: column; align-items: center; gap: 10px;
    background: var(--card); transition: all .2s ease; cursor: pointer;
  }
  .upload-zone.drag-over { border-color: var(--primary); background: #e4f2ea; transform: scale(1.005); }
  .upload-icon-wrap {
    width: 60px; height: 60px; border-radius: 16px; background: #e4f2ea;
    color: var(--primary); display: flex; align-items: center; justify-content: center; margin-bottom: 6px;
  }
  .upload-title { font-weight: 600; font-size: 15px; }
  .upload-sub { color: var(--muted); font-size: 12px; margin: 0; }
  .supported-types { display: flex; gap: 6px; margin-top: 10px; }
  .type-chip { font-size: 11px; padding: 3px 8px; border-radius: 999px; background: var(--bg); color: var(--muted); border: 1px solid var(--border); }

  .btn-primary, .btn-secondary, .btn-ghost {
    display: inline-flex; align-items: center; gap: 6px; border-radius: 10px; font-size: 13px;
    font-weight: 600; border: none; padding: 9px 16px; transition: all .15s ease;
  }
  .btn-primary { background: var(--primary); color: white; }
  .btn-primary:hover { background: var(--accent); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-secondary { background: var(--bg); color: var(--text); border: 1px solid var(--border); }
  .btn-secondary:hover { background: var(--primary); color: white; border-color: transparent; }
  .btn-ghost { background: transparent; color: var(--muted); border: 1px solid var(--border); }
  .btn-ghost:hover { color: var(--text); border-color: var(--text); }
  .btn-ghost.small { padding: 6px 10px; font-size: 12px; }
  .btn-ghost.active { background: var(--primary); color: white; border-color: transparent; }

  .upload-stats {
    display: flex; align-items: center; gap: 20px; margin-top: 20px; padding: 16px 20px;
    background: var(--card); border-radius: 14px; border: 1px solid var(--border);
  }
  .stat-block { display: flex; flex-direction: column; }
  .stat-value { font-weight: 700; font-size: 17px; }
  .stat-label { font-size: 11px; color: var(--muted); }
  .stat-divider { width: 1px; height: 28px; background: var(--border); }
  .upload-actions { margin-left: auto; display: flex; gap: 10px; }

  /* Processing panel */
  .processing-panel { background: var(--card); border-radius: 18px; padding: 28px; border: 1px solid var(--border); }
  .panel-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 18px; }
  .panel-header h2 { margin: 0; font-size: 18px; }
  .panel-elapsed { font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }
  .progress-track { height: 8px; border-radius: 999px; background: var(--bg); overflow: hidden; }
  .progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--primary)); transition: width .35s ease; border-radius: 999px; }
  .progress-meta { display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); margin: 8px 0 22px; }

  .stage-timeline { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
  .stage-row { display: flex; align-items: center; gap: 10px; color: var(--muted); font-size: 13px; }
  .stage-row.done { color: var(--success); }
  .stage-row.active { color: var(--primary); font-weight: 600; }
  .stage-icon { opacity: 0.7; }
  .spin { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Results */
  .results-section { margin-top: 8px; }
  .results-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .results-header h2 { margin: 0; font-size: 18px; }
  .group-list { display: flex; flex-direction: column; gap: 14px; }

  .group-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 16px 18px; transition: box-shadow .2s ease; }
  .group-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.05); }
  .group-card-top { display: flex; align-items: center; gap: 14px; }
  .group-thumb-preview {
    width: 44px; height: 44px; border-radius: 12px; background: #e4f2ea;
    color: var(--primary); border: none; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .group-info { flex: 1; min-width: 0; }
  .group-name-row { display: flex; align-items: center; gap: 6px; }
  .group-name-row h3 { margin: 0; font-size: 15px; font-weight: 600; }
  .group-name-input { font-size: 15px; font-weight: 600; border: 1px solid var(--primary); border-radius: 6px; padding: 2px 6px; background: var(--bg); color: var(--text); }
  .group-meta-row { display: flex; gap: 10px; align-items: center; margin-top: 4px; font-size: 12px; color: var(--muted); flex-wrap: wrap; }
  .confidence-chip { background: #e4f2ea; color: var(--primary); padding: 2px 8px; border-radius: 999px; }
  .reviewed-badge { display: flex; align-items: center; gap: 3px; color: var(--success); }
  .group-card-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

  .group-card-body { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--border); }
  .thumb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 10px; }
  .thumb-cell { position: relative; }
  .thumb-frame {
    width: 100%; aspect-ratio: 1; border-radius: 10px; border: 1px solid var(--border);
    background: var(--bg); display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden;
  }
  .thumb-art { color: var(--muted); display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
  .thumb-art.bg-removed { background: repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50% / 12px 12px; }
  .thumb-tag { position: absolute; bottom: 4px; left: 4px; font-size: 9px; background: var(--primary); color: white; padding: 1px 5px; border-radius: 6px; }
  .thumb-controls { position: absolute; top: 4px; right: 4px; display: flex; gap: 3px; }
  .thumb-select, .thumb-delete {
    width: 22px; height: 22px; border-radius: 6px; border: none; background: rgba(255,255,255,0.9);
    display: flex; align-items: center; justify-content: center; color: var(--text);
  }
  .thumb-delete:hover { background: var(--error); color: white; }
  .thumb-select:hover { background: var(--primary); color: white; }

  /* Empty state */
  .empty-state { text-align: center; padding: 60px 20px; color: var(--muted); }
  .empty-icon { width: 52px; height: 52px; border-radius: 14px; background: var(--card); display: flex; align-items: center; justify-content: center; margin: 0 auto 14px; border: 1px solid var(--border); }
  .empty-state h3 { color: var(--text); margin: 0 0 6px; }
  .empty-state p { margin: 0; font-size: 13px; }

  /* Export footer */
  .export-footer {
    position: sticky; bottom: 0; z-index: 15; background: var(--card); border-top: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between; padding: 16px 28px;
    box-shadow: 0 -8px 24px rgba(0,0,0,0.05); flex-wrap: wrap; gap: 12px;
  }
  .export-stats { display: flex; gap: 24px; }
  .export-stat { display: flex; flex-direction: column; }
  .export-stat-value { font-weight: 700; font-size: 16px; }
  .export-stat-label { font-size: 11px; color: var(--muted); }
  .export-actions { display: flex; gap: 10px; }

  /* Modal */
  .modal-overlay { position: fixed; inset: 0; background: rgba(20,17,14,0.85); z-index: 100; display: flex; align-items: center; justify-content: center; animation: fadeIn .15s ease; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  .modal-shell { position: relative; width: min(90vw, 900px); height: min(80vh, 640px); background: #111; border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; }
  .modal-close { position: absolute; top: 14px; right: 14px; z-index: 5; background: rgba(255,255,255,0.1); border: none; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
  .modal-nav { position: absolute; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.1); border: none; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 5; }
  .modal-nav-left { left: 14px; } .modal-nav-right { right: 14px; }
  .modal-nav:hover, .modal-close:hover { background: rgba(255,255,255,0.22); }
  .modal-canvas { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; cursor: grab; }
  .modal-art { color: rgba(255,255,255,0.75); transition: transform .1s linear; display: flex; align-items: center; justify-content: center; width: auto; height: 80%; border-radius: 12px; background: transparent; }
  .modal-art.bg-removed { background: repeating-conic-gradient(#333 0% 25%, #222 0% 50%) 50% / 16px 16px; }
  .modal-toolbar { display: flex; align-items: center; gap: 8px; justify-content: center; padding: 10px; background: rgba(255,255,255,0.04); }
  .modal-toolbar .icon-btn { border-color: rgba(255,255,255,0.15); color: white; }
  .zoom-value { color: white; font-size: 12px; min-width: 38px; text-align: center; }
  .toolbar-divider { width: 1px; height: 18px; background: rgba(255,255,255,0.15); }
  .modal-meta { display: flex; gap: 16px; justify-content: center; padding: 8px; font-size: 11px; color: rgba(255,255,255,0.55); }

  @media (max-width: 640px) {
    .topnav { padding: 12px 16px; }
    .app-main { padding: 24px 14px 120px; }
    .hero-copy h1 { font-size: 22px; }
    .upload-stats { flex-wrap: wrap; }
    .upload-actions { margin-left: 0; width: 100%; justify-content: flex-end; }
    .export-footer { padding: 12px 16px; }
    .export-stats { gap: 14px; }
  }
`;
