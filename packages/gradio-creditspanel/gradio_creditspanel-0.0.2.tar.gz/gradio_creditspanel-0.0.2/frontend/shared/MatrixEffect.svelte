<script lang="ts">
    import { onMount, onDestroy } from 'svelte';

    /**
     * Props for the MatrixEffect component.
     * @typedef {Object} Props
     * @property {Array<{title: string, name: string}>} credits - List of credits with title and name.
     * @property {number} speed - Animation speed in seconds (default: 20).
     * @property {number} base_font_size - Base font size in em (default: 1.0).
     * @property {string | null} intro_title - Optional intro title.
     * @property {string | null} intro_subtitle - Optional intro subtitle.
     */
    export let credits: Props['credits'];
    export let speed: number = 20;
    export let base_font_size: number = 1.0;
    export let intro_title: string | null = null;
    export let intro_subtitle: string | null = null;

    // Combines intro and credits for display
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

    // Reactive font size styles
    $: title_style = (is_intro: boolean) => `font-size: ${is_intro ? base_font_size * 1.2 : base_font_size * 0.8}em;`;
    $: name_style = (is_intro: boolean) => `font-size: ${is_intro ? base_font_size * 1.5 : base_font_size}em;`;

    // Canvas setup for Matrix effect
    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D;
    let contentElement: HTMLElement | null;
    const fontSize = 16;
    const characters = 'アァカサタナハマヤャラワガザダバパイィキシチニヒミリヰギジヂビピウゥクスツヌフムユュルグズブヅプエェケセテネヘメレヱゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴッン01';
    let columns: number;
    let drops: number[] = [];
    let animationFrameId: number;

    // Initialize canvas and drops
    function setup() {
        if (!canvas) return;
        const parent = canvas.parentElement;
        if (parent) {
            canvas.width = parent.clientWidth;
            canvas.height = parent.clientHeight;
        }
        ctx = canvas.getContext('2d')!;
        columns = Math.floor(canvas.width / fontSize);
        drops = Array(columns).fill(1);
    }

    // Draw Matrix falling characters
    function drawMatrix() {
        if (!ctx) return;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#0F0';
        ctx.font = `${fontSize}px monospace`;
        for (let i = 0; i < drops.length; i++) {
            const text = characters.charAt(Math.floor(Math.random() * characters.length));
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
        animationFrameId = requestAnimationFrame(drawMatrix);
    }

    // Reset credits animation
    function resetCreditsAnimation() {
        if (contentElement) {
            contentElement.style.animation = 'none';
            void contentElement.offsetHeight; // Trigger reflow
            contentElement.style.animation = '';
        }
    }

    // Setup canvas and animation on mount
    onMount(() => {
        setup();
        drawMatrix();
        resetCreditsAnimation();
        const resizeObserver = new ResizeObserver(() => {
            cancelAnimationFrame(animationFrameId);
            setup();
            drawMatrix();
        });
        if (canvas.parentElement) {
            resizeObserver.observe(canvas.parentElement);
        }
        return () => {
            cancelAnimationFrame(animationFrameId);
            if (canvas.parentElement) {
                resizeObserver.unobserve(canvas.parentElement);
            }
        };
    });

    // Reset animation on prop changes
    $: credits, speed, intro_title, intro_subtitle, resetCreditsAnimation();

    // Cleanup on destroy
    onDestroy(() => {
        contentElement = null;
    });
</script>

<div class="matrix-container">
    <canvas bind:this={canvas}></canvas>
    <div class="credits-scroll-overlay">
        <div class="credits-content" bind:this={contentElement} style="--animation-duration: {speed}s;">
            {#each display_items as item}
                <div class="credit-block" class:intro-block={item.is_intro}>
                    <div style={title_style(item.is_intro)} class="title">{item.title}</div>
                    {#if item.name}
                        <div style={name_style(item.is_intro)} class="name">{item.name}</div>
                    {/if}
                </div>
            {/each}
        </div>
    </div>
</div>

<style>
    /* Container for Matrix effect */
    .matrix-container {
        width: 100%;
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    /* Canvas for falling characters */
    canvas {
        display: block;
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
    }
    /* Overlay for scrolling credits */
    .credits-scroll-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 2;
        color: #fff;
        font-family: monospace;
        text-align: center;
        -webkit-mask-image: linear-gradient(transparent, black 20%, black 80%, transparent);
        mask-image: linear-gradient(transparent, black 20%, black 80%, transparent);
    }
    /* Scrolling credits container */
    .credits-content {
        position: absolute;
        width: 100%;
        bottom: 0;
        transform: translateY(100%);
        animation: scroll-from-bottom var(--animation-duration) linear infinite;
    }
    @keyframes scroll-from-bottom {
        from { transform: translateY(100%); }
        to { transform: translateY(-100%); }
    }
    /* Intro block spacing */
    .credit-block.intro-block { margin-bottom: 5rem; }
    /* Credit block spacing */
    .credit-block { margin-bottom: 2.5em; }
    /* Title styling */
    .title {
        color: #0F0;
        text-transform: uppercase;
        opacity: 0.8;
    }
    /* Name styling */
    .name {
        font-weight: bold;
        color: #5F5;
        text-shadow: 0 0 5px #0F0;
    }
</style>