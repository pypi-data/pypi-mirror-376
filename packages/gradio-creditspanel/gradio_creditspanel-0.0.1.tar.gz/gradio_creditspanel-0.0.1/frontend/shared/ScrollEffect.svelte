<script lang="ts">
    /**
     * Props for the ScrollEffect component.
     * @typedef {Object} Props
     * @property {Array<{title: string, name: string}>} credits - List of credits with title and name.
     * @property {number} speed - Animation speed in seconds.
     * @property {number} base_font_size - Base font size in rem (default: 1.5).
     * @property {string | null} background_color - Background color (default: black).
     * @property {string | null} title_color - Title text color (default: white).
     * @property {string | null} name_color - Name text color (default: white).
     * @property {string | null} intro_title - Optional intro title.
     * @property {string | null} intro_subtitle - Optional intro subtitle.
     */
    export let credits: Props['credits'];
    export let speed: number;
    export let base_font_size: number = 1.5;
    export let background_color: string | null = null;
    export let title_color: string | null = null;
    export let name_color: string | null = null;
    export let intro_title: string | null = null;
    export let intro_subtitle: string | null = null;

    // Flag to trigger animation reset
    let reset = false;

    // Combine intro and credits for display
    $: display_items = (() => {
        const items = [];
        if (intro_title || intro_subtitle) {
            items.push({ 
                title: intro_title || '', 
                name: intro_subtitle || '',
                is_intro: true
            });
        }
        return [...items, ...credits.map(c => ({ ...c, is_intro: false }))];
    })();

    // Reactive styles for title and name
    $: title_style = (is_intro: boolean) => `color: ${title_color || 'white'}; font-size: ${is_intro ? base_font_size * 1.5 : base_font_size}rem;`;
    $: name_style = (is_intro: boolean) => `color: ${name_color || 'white'}; font-size: ${is_intro ? base_font_size * 0.9 : base_font_size * 0.8}rem;`;

    // Reset animation on prop changes
   function resetAnimation() {
        reset = true;
        setTimeout(() => (reset = false), 0);
    }



    // Trigger reset on prop changes
    $: credits, speed, resetAnimation();
</script>

<div class="wrapper" style:--animation-duration="{speed}s" style:background={background_color || 'black'}>
    {#if !reset}
        <div class="credits-container">
            {#each display_items as item}
                <div class="credit" class:intro-block={item.is_intro}>
                    <h2 style={title_style(item.is_intro)}>{item.title}</h2>
                    {#if item.name}<p style={name_style(item.is_intro)}>{item.name}</p>{/if}
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    /* Container for scrolling credits */
    .wrapper {
        width: 100%;
        height: 100%;
        overflow: hidden;
        position: relative;
        font-family: sans-serif;
    }
    /* Intro block styling */
    .credit.intro-block {
        margin-bottom: 5rem;
        text-align: center;
    }
    /* Credits container with scroll animation */
    .credits-container {
        position: absolute;
        bottom: 0;
        transform: translateY(100%);
        width: 100%;
        text-align: center;
        animation: scroll var(--animation-duration) linear infinite;
    }
    /* Individual credit block */
    .credit {
        margin-bottom: 2rem;
    }
    .credit h2 {
        margin: 0.5rem 0;
        font-family: sans-serif;
    }
    .credit p {
        margin: 0.5rem 0;
        font-family: sans-serif;
    }
    /* Scroll animation keyframes */
    @keyframes scroll {
        0% { transform: translateY(100%); }
        100% { transform: translateY(-100%); }
    }
</style>