import { useEffect, useState } from "react";
import { api } from "../api/client";
type P = { id: number; name: string; ferment_min: number; bake_min: number; temp_profile: string };
const PROFILES = ["低温", "中温", "高温"];
export default function ProductsPage() {
  const [rows, setRows] = useState<P[]>([]);
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => { api<P[]>("/products").then(setRows); }, []);
  async function changeProfile(p: P, temp_profile: string) {
    setMsg(""); setErr("");
    try {
      const updated = await api<P>(`/products/${p.id}`, { method: "PATCH", body: JSON.stringify({ temp_profile }) });
      setRows(rs => rs.map(r => r.id === updated.id ? updated : r));
      setMsg(`已保存 ${updated.name} 温度档：${updated.temp_profile}`);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>产品（配方时长 · 温度档）</h2>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <table className="table"><thead><tr><th>名称</th><th>发酵 min</th><th>烘烤 min</th><th>合计</th><th>温度档</th></tr></thead>
    <tbody>{rows.map(p => <tr key={p.id}><td>{p.name}</td><td className="mono">{p.ferment_min}</td><td className="mono">{p.bake_min}</td><td className="mono">{p.ferment_min + p.bake_min}</td>
      <td><select value={p.temp_profile} onChange={e => changeProfile(p, e.target.value)}>
        {(PROFILES.includes(p.temp_profile) ? PROFILES : [p.temp_profile, ...PROFILES]).map(t => <option key={t} value={t}>{t}</option>)}
      </select></td></tr>)}</tbody></table>
  </>);
}


