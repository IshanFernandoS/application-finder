"use client";

import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable, type ColumnDef } from "@tanstack/react-table";
import type { MaterialCandidate } from "@/lib/types";

const columns: ColumnDef<MaterialCandidate>[] = [
  { accessorKey: "material", header: "Material" },
  { accessorKey: "material_class", header: "Class" },
  { accessorKey: "role_in_device", header: "Role" },
  { accessorKey: "evidence_strength", header: "Evidence", cell: (ctx) => `${Math.round(Number(ctx.getValue()) * 100)}%` },
  { accessorKey: "validation_status", header: "Validation" },
  { accessorKey: "source", header: "Source" },
  { accessorKey: "confidence", header: "Confidence", cell: (ctx) => `${Math.round(Number(ctx.getValue()) * 100)}%` },
  { accessorKey: "next_validation_step", header: "Next step" }
];

export function MaterialCandidateTable({ candidates = [] }: { candidates?: MaterialCandidate[] }) {
  const table = useReactTable({ data: candidates, columns, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel() });
  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-line px-5 py-4">
        <h2 className="text-base font-semibold">Material Candidates</h2>
      </div>
      <div className="overflow-auto scrollbar">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-shell text-xs text-muted">
            {table.getHeaderGroups().map((group) => (
              <tr key={group.id}>
                {group.headers.map((header) => (
                  <th key={header.id} className="whitespace-nowrap px-4 py-3 font-medium">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-t border-line">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="max-w-72 px-4 py-3 align-top text-muted">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
