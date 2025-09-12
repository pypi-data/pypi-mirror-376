<script lang="ts">
    import { onMount, onDestroy } from 'svelte';

    /**
     * Props for the StarWarsEffect component.
     * @typedef {Object} Props
     * @property {Array<{title: string, name: string}>} credits - List of credits with title and name.
     * @property {number} speed - Animation speed in seconds (default: 40).
     * @property {number} base_font_size - Base font size in rem (default: 1.5).
     * @property {string | null} background_color - Background color (default: black).
     * @property {string | null} title_color - Title text color (default: #feda4a).
     * @property {string | null} name_color - Name text color (default: #feda4a).
     * @property {string | null} intro_title - Optional intro title.
     * @property {string | null} intro_subtitle - Optional intro subtitle.
     */
    export let credits: Props['credits'];
    export let speed: number = 40;
    export let base_font_size: number = 1.5;
    export let background_color: string | null = null;
    export let title_color: string | null = null;
    export let name_color: string | null = null;
    export let intro_title: string | null = null;
    export let intro_subtitle: string | null = null;

    // Reactive styles for title and name
    $: title_style = (is_intro: boolean) => `color: ${title_color || '#feda4a'}; font-size: ${is_intro ? base_font_size * 1.5 : base_font_size}rem !important;`;
    $: name_style = (is_intro: boolean) => `color: ${name_color || '#feda4a'}; font-size: ${is_intro ? base_font_size * 0.9 : base_font_size * 0.7}rem !important;`;

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

    // Element for animation reset
    let crawlElement: HTMLElement | null;

    // Reset animation on prop changes
    function resetAnimation() {
        if (crawlElement) {
            crawlElement.style.animation = 'none';
            void crawlElement.offsetHeight; // Trigger reflow
            crawlElement.style.animation = '';
        }
    }

    // Initialize animation on mount
    onMount(() => {
        resetAnimation();
        return () => {};
    });

    // Trigger reset on prop changes
    $: credits, speed, base_font_size, background_color, title_color, name_color, intro_title, intro_subtitle, resetAnimation();

    // Cleanup on destroy
    onDestroy(() => {
        crawlElement = null;
    });

    // Generate star shadows for background
    const generate_star_shadows = (count: number, size: string) => {
        let shadows = '';
        for (let i = 0; i < count; i++) {
            shadows += `${Math.random() * 2000}px ${Math.random() * 2000}px ${size} white, `;
        }
        return shadows.slice(0, -2);
    };

    const small_stars = generate_star_shadows(200, '1px');
    const medium_stars = generate_star_shadows(100, '2px');
    const large_stars = generate_star_shadows(50, '3px');
</script>

<div class="viewport" style:background={background_color || 'black'}>
    <!-- Star layers for background -->
    <div class="stars small" style="box-shadow: {small_stars};"></div>
    <div class="stars medium" style="box-shadow: {medium_stars};"></div>
    <div class="stars large" style="box-shadow: {large_stars};"></div>

    <!-- Crawling credits -->
    <div class="crawl" bind:this={crawlElement} style="--animation-duration: {speed}s;">
        {#each display_items as item}
            <div class="credit" class:intro-block={item.is_intro}>
                <h2 style={title_style(item.is_intro)}>{item.title}</h2>
                {#if item.name}<p style={name_style(item.is_intro)}>{item.name}</p>{/if}
            </div>
        {/each}
    </div>
</div>

<style>
    /* Container with perspective for 3D effect */
    .viewport {
        width: 100%;
        height: 100%;
        position: relative;
        overflow: hidden;
        perspective: 400px;
        -webkit-mask-image: linear-gradient(to bottom, black 60%, transparent 100%);
        mask-image: linear-gradient(to bottom, black 60%, transparent 100%);
        font-family: "Droid Sans", sans-serif;
        font-weight: bold;
    }
    /* Star layers with twinkling animation */
    .stars {
        position: absolute;
        top: 0;
        left: 0;
        width: 1px;
        height: 1px;
        background: transparent;
        z-index: 0;
        animation: twinkle 10s linear infinite;
    }
    .stars.small { animation-duration: 10s; }
    .stars.medium { animation-duration: 15s; }
    .stars.large { animation-duration: 20s; }
    @keyframes twinkle {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    /* Crawling text container */
    .crawl {
        position: absolute;
        width: 100%;
        bottom: 0;
        transform-origin: 50% 100%;
        animation: crawl-animation var(--animation-duration) linear infinite;
        z-index: 1;
        text-align: center;
    }
    /* Crawl animation with 3D transform */
    @keyframes crawl-animation {
        0% { transform: rotateX(60deg) translateY(100%) translateZ(100px); opacity: 1; }
        100% { transform: rotateX(60deg) translateY(-150%) translateZ(-1200px); opacity: 1; }
    }
    /* Intro block spacing */
    .credit.intro-block { margin-bottom: 5rem; }
    /* Credit block spacing */
    .credit { margin-bottom: 2rem; }
    /* Text styling */
    h2, p {
        margin: 0.5rem 0;
        padding: 0;
        white-space: nowrap;
    }
</style>