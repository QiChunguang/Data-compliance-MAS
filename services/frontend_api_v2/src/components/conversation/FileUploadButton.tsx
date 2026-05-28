type Props = {
  disabled: boolean;
  onUpload: (file: File) => void;
};

export function FileUploadButton({ disabled, onUpload }: Props) {
  return (
    <label className={disabled ? "file-upload disabled" : "file-upload"}>
      上传材料
      <input
        disabled={disabled}
        type="file"
        accept=".txt,.md,.json,.csv,.pdf,.docx,.xlsx"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            onUpload(file);
            event.currentTarget.value = "";
          }
        }}
      />
    </label>
  );
}
