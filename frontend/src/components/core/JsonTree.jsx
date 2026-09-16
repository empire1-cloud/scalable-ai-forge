import { createElement } from "react";

export default function JsonTree({ data }) {
  if (data == null) return null;
  const entries = Object.entries(data);
  return (
    <div data-testid="json-tree" className="space-y-3">
      {entries.map(([k, v]) => (
        <TreeNode key={k} label={k} value={v} depth={0} />
      ))}
    </div>
  );
}

function TreeNode({ label, value, depth }) {
  const title = label.replace(/_/g, " ");
  const pad = depth ? "p-3" : "p-4";
  const isObj = typeof value === "object" && value !== null;

  if (Array.isArray(value)) {
    return (
      <div className={`rounded-lg border border-slate-800 bg-[#070A0F] ${pad}`}>
        <Heading text={title} count={value.length} />
        <div className="mt-2 space-y-2">
          {value.map((item, i) => (
            <ArrayItem key={i} item={item} />
          ))}
        </div>
      </div>
    );
  }

  if (isObj) {
    const entries = Object.entries(value);
    return (
      <div className={`rounded-lg border border-slate-800 bg-[#070A0F] ${pad}`}>
        <Heading text={title} />
        <div className="mt-2 space-y-2">
          {entries.map(([k, v]) =>
            createElement(TreeNode, { key: k, label: k, value: v, depth: depth + 1 })
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-800 bg-[#070A0F] p-4">
      <Heading text={title} />
      <p className="mt-1.5 text-slate-200 leading-relaxed whitespace-pre-wrap">{String(value)}</p>
    </div>
  );
}

function ArrayItem({ item }) {
  if (typeof item === "object" && item !== null) {
    const entries = Object.entries(item);
    return (
      <div className="rounded border border-slate-800/70 bg-[#0D131E] p-3 space-y-1.5">
        {entries.map(([ik, iv]) => (
          <Leaf key={ik} label={ik} value={iv} />
        ))}
      </div>
    );
  }
  return (
    <div className="text-sm text-slate-300 flex gap-2">
      <span className="text-cyan-400">▸</span>
      <span>{String(item)}</span>
    </div>
  );
}

function Heading({ text, count }) {
  return (
    <div className="font-mono text-[10px] tracking-widest uppercase text-cyan-400 flex items-center gap-2">
      {text}
      {count != null && <span className="text-slate-500">({count})</span>}
    </div>
  );
}

function Leaf({ label, value }) {
  const isCode = label === "content" || label === "code";
  if (Array.isArray(value)) {
    return (
      <div>
        <LeafLabel text={label} />
        <span className="text-sm text-slate-300">{value.map(String).join(" · ")}</span>
      </div>
    );
  }
  if (typeof value === "object" && value !== null) {
    return (
      <div>
        <LeafLabel text={label} />
        <pre className="text-xs font-mono text-slate-400 mt-1">{JSON.stringify(value, null, 2)}</pre>
      </div>
    );
  }
  if (isCode && typeof value === "string" && value.includes("\n")) {
    return (
      <pre className="p-3 rounded bg-[#05070B] border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto max-h-[360px]">
        <code>{value}</code>
      </pre>
    );
  }
  return (
    <div className="text-sm">
      <LeafLabel text={label} />
      <span className="text-slate-200">{String(value)}</span>
    </div>
  );
}

function LeafLabel({ text }) {
  return (
    <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500 mr-2">{text}</span>
  );
}
