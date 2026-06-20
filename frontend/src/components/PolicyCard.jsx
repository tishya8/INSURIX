function PolicyCard({
  policyId,
  title,
  selected,
  onClick
}) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: "12px",
        borderRadius: "10px",
        marginBottom: "10px",
        cursor: "pointer",
        background:
          selected
            ? "#2563eb"
            : "#374151",
        color: "white"
      }}
    >
      <strong>
        {policyId}
      </strong>

      <br />

      <span
        style={{
          fontSize: "13px"
        }}
      >
        {title}
      </span>

      <br />

      <span
        style={{
          fontSize: "12px"
        }}
      >
        Active
      </span>
    </div>
  );
}

export default PolicyCard;