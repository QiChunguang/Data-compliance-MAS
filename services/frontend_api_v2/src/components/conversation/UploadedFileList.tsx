import type { UploadedFile } from "../../types/reguthink-interactive-api";

export function UploadedFileList({ files }: { files: UploadedFile[] }) {
  return (
    <section className="wb-mini-panel">
      <h3>Uploaded Materials</h3>
      {files.length === 0 ? (
        <div className="wb-placeholder">No uploaded files. Uploads remain outside Chroma / Neo4j / legal_data.</div>
      ) : (
        <div className="uploaded-file-list">
          {files.map((file) => (
            <article key={file.file_id}>
              <strong>{file.original_filename}</strong>
              <span>{file.parse_status}</span>
              <span>{file.size_bytes} bytes</span>
              <span>sha256 {file.sha256.slice(0, 16)}...</span>
              <small>{file.display_path}</small>
              {file.extraction_warning && <em>{file.extraction_warning}</em>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
