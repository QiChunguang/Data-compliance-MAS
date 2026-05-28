type Props = {
  status: string;
  message: string;
};

export function RuntimeFailureNotice({ status, message }: Props) {
  return (
    <section className="runtime-failure-notice">
      <h3>Real Runtime Not Completed</h3>
      <p>{status}</p>
      <pre>{message}</pre>
      <span>下一步建议：确认 core/v12 单 case runtime 契约、输出目录和数据库写入边界后再启用 controlled runtime。</span>
    </section>
  );
}
