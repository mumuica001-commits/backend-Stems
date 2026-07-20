"use client"

import { useSearchParams } from "next/navigation"

export default function JobPage() {
  const searchParams = useSearchParams()
  const id = searchParams.get("id")

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 text-white p-6">
      <div className="max-w-md w-full bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center shadow-lg">
        <h1 className="text-xl font-bold mb-2 text-indigo-400">Áudio Enviado com Sucesso!</h1>
        <p className="text-zinc-400 text-sm mb-4">O seu job está na fila do servidor.</p>
        
        <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800 font-mono text-xs text-zinc-500 break-all">
          ID: {id || "Nenhum ID encontrado na URL"}
        </div>
        
        <div className="mt-6 flex items-center justify-center gap-2 text-sm text-zinc-400">
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>
          Conectando ao servidor para acompanhar o progresso...
        </div>
      </div>
    </div>
  )
}