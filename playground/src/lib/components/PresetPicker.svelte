<script lang="ts">
  import type { Preset } from "../types.js";

  let {
    presets,
    active,
    onselect,
  }: {
    presets: Preset[];
    active: string;
    onselect: (preset: Preset) => void;
  } = $props();
</script>

<div class="preset-picker">
  <div class="label">Presets</div>
  <div class="pills">
    {#each presets as preset}
      <button
        class="pill"
        class:active={active === preset.id}
        onclick={() => onselect(preset)}
        title={preset.description}
      >
        {preset.name}
      </button>
    {/each}
  </div>
</div>

<style>
  .preset-picker {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .pill {
    background: var(--bg-elevated);
    color: var(--text-muted);
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    transition:
      background 0.15s,
      color 0.15s;
  }

  .pill:hover {
    background: color-mix(in srgb, var(--accent) 15%, var(--bg-elevated));
    color: var(--text);
  }

  .pill.active {
    background: color-mix(in srgb, var(--accent) 20%, var(--bg-elevated));
    color: var(--accent);
    outline: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
  }
</style>
