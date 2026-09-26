import { useEffect, useState } from "react";
import { api } from "../api/client";
type O = { id: number; label: string; capacity_note: string; preheat_min: number };
export default function OvensPage() {
  const [rows, setRows] = useState<O[]>([]);
  const [draft, setDraft] = useState<Record<number, number>>({});
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => {
    api<O[]>("/ovens").then(os => {
      setRows(os);
      setDraft(Object.fromEntries(os.map(o => [o.id, o.preheat_min])));
    });
  }, []);
  async function save(o: O) {
    setMsg(""); setErr("");
    try {
      const updated = await api<O>(`/ovens/${o.id}`, { method: "PATCH", body: JSON.stringify({ preheat_min: draft[o.id] ?? o.preheat_min }) });
      setRows(rs => rs.map(r => r.id === updated.id ? updated : r));
      setMsg(`已保存 ${updated.label} 预热 ${updated.preheat_min} 分钟`);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>炉位</h2>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <table className="table"><thead><tr><th>标签</th><th>备注</th><th>换档预热 min</th><th></th></tr></thead>
    <tbody>{rows.map(o => <tr key={o.id}><td>{o.label}</td><td>{o.capacity_note}</td>
      <td><input type="number" min={0} max={240} value={draft[o.id] ?? o.preheat_min}
        onChange={e => setDraft(d => ({ ...d, [o.id]: Number(e.target.value) }))} style={{ width: 80 }} /></td>
      <td><button onClick={() => save(o)}>保存</button></td></tr>)}</tbody></table>
  </>);
}


