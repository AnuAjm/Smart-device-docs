document.addEventListener("DOMContentLoaded", async () => {
  await mermaid.run({
    querySelector: ".mermaid"
  });
});