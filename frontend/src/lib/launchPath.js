// Launch Path helpers shared by the blueprint page and the .md export.
// Plain JS (no JSX) so the markdown can also be produced outside the app.

export const COST_NOTE = "Unverified: check current pricing before you rely on it.";

// Only ever link to https URLs from model output (never javascript: etc).
export function safeUrl(url) {
  return typeof url === "string" && /^https:\/\/[^\s]+$/i.test(url) ? url : null;
}

export function launchPathMarkdown(lp, check) {
  const lines = [`\n## Launch Path`];
  if (!lp) {
    lines.push(
      "\n_This blueprint was made before Launch Path existed, so it has no step-by-step instructions. Regenerate it to get them._"
    );
    return lines.join("\n");
  }
  if (lp.goal) lines.push(`\n**Done looks like:** ${lp.goal}`);
  if (lp.time_estimate) lines.push(`\n**Time:** ${lp.time_estimate}`);

  if (check && check.problems?.length) {
    lines.push(`\n### Self-check found gaps`);
    check.problems.forEach((p) => lines.push(`- ${p}`));
  }

  if (lp.accounts?.length) {
    lines.push(`\n### What you'll need`);
    lp.accounts.forEach((a) => {
      const url = safeUrl(a.signup_url);
      lines.push(`- **${a.name}** (${url || "no link"}): ${a.why}`);
      if (a.cost) lines.push(`  - Cost: ${a.cost} _(${COST_NOTE})_`);
    });
  }

  if (lp.steps?.length) {
    lines.push(`\n### Steps`);
    lp.steps.forEach((s, i) => {
      lines.push(`\n${i + 1}. **${s.step}**`);
      if (s.do) lines.push(`   ${s.do}`);
      if (s.uses_files?.length) lines.push(`   Files: ${s.uses_files.map((f) => `\`${f}\``).join(", ")}`);
      if (s.check) lines.push(`   ✓ You'll know it worked when: ${s.check}`);
    });
  }

  if (lp.done_test) lines.push(`\n### Final test\n${lp.done_test}`);

  if (lp.if_it_breaks?.length) {
    lines.push(`\n### If it breaks`);
    lp.if_it_breaks.forEach((b) => lines.push(`- **${b.symptom}** ${b.fix}`));
  }

  if (lp.not_included?.length) {
    lines.push(`\n### Not built yet`);
    lp.not_included.forEach((n) => lines.push(`- ${n}`));
  }
  return lines.join("\n");
}
