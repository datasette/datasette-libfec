import * as d3Sankey from 'd3-sankey';
import * as d3 from 'd3';

/* eslint-disable @typescript-eslint/no-explicit-any */

// Copyright 2021-2023 Observable, Inc.
// Released under the ISC license.
// https://observablehq.com/@d3/sankey-diagram

interface InputNode {
	id: string | number;
	[key: string]: any;
}

interface InputLink {
	source: string | number;
	target: string | number;
	value: number;
	[key: string]: any;
}

type NodeAlign = 'left' | 'right' | 'center' | 'justify' | ((node: any, n: number) => number);

interface SankeyChartOptions {
	format?: string | ((d: any) => string);
	align?: NodeAlign;
	nodeId?: (d: any) => any;
	nodeGroup?: ((d: any) => any) | undefined;
	nodeGroups?: any[] | undefined;
	nodeLabel?: ((d: any) => string | string[]) | undefined;
	nodeTitle?: ((d: any) => string) | null;
	nodeAlign?: NodeAlign;
	nodeSort?: ((a: any, b: any) => number) | undefined;
	nodeWidth?: number;
	nodePadding?: number;
	nodeLabelPadding?: number;
	nodeStroke?: string;
	nodeStrokeWidth?: number;
	nodeStrokeOpacity?: number;
	nodeStrokeLinejoin?: string;
	linkSource?: (d: any) => any;
	linkTarget?: (d: any) => any;
	linkValue?: (d: any) => number;
	linkPath?: any;
	linkTitle?: ((d: any) => string) | null;
	linkColor?: string;
	linkStrokeOpacity?: number;
	linkMixBlendMode?: string;
	colors?: readonly string[];
	width?: number;
	height?: number;
	marginTop?: number;
	marginRight?: number;
	marginBottom?: number;
	marginLeft?: number;
	onClick?: ((d: any) => void) | undefined;
}

export function SankeyChart(
	{
		nodes, // an iterable of node objects (typically [{id}, …]); implied by links if missing
		links // an iterable of link objects (typically [{source, target}, …])
	}: {
		nodes?: InputNode[];
		links: InputLink[];
	},
	{
		format = ',' as string | ((d: any) => string), // a function or format specifier for values in titles
		align = 'justify' as NodeAlign, // convenience shorthand for nodeAlign
		nodeId = (d: any) => d.id, // given d in nodes, returns a unique identifier (string)
		nodeGroup = undefined as any, // given d in nodes, returns an (ordinal) value for color
		nodeGroups = undefined as any, // an array of ordinal values representing the node groups
		nodeLabel = undefined as any, // given d in (computed) nodes, text to label the associated rect
		nodeTitle = (d: any) => `${typeof format === 'function' ? format(d.value) : d3.format(format)(d.value)}`, // given d in (computed) nodes, hover text
		nodeAlign = align, // Sankey node alignment strategy: left, right, justify, center
		nodeSort = undefined as ((a: any, b: any) => number) | undefined, // comparator function to order nodes
		nodeWidth = 15, // width of node rects
		nodePadding = 10, // vertical separation between adjacent nodes
		nodeLabelPadding = 6, // horizontal separation between node and label
		nodeStroke = 'currentColor', // stroke around node rects
		nodeStrokeWidth = undefined as number | undefined, // width of stroke around node rects, in pixels
		nodeStrokeOpacity = undefined as number | undefined, // opacity of stroke around node rects
		nodeStrokeLinejoin = undefined as string | undefined, // line join for stroke around node rects
		linkSource = ({ source }: any) => source, // given d in links, returns a node identifier string
		linkTarget = ({ target }: any) => target, // given d in links, returns a node identifier string
		linkValue = ({ value }: any) => value, // given d in links, returns the quantitative value
		linkPath = d3Sankey.sankeyLinkHorizontal(), // given d in (computed) links, returns the SVG path
		linkTitle = (d: any) => `${d.source.id} → ${d.target.id}\n${typeof format === 'function' ? format(d.value) : d3.format(format)(d.value)}`, // given d in (computed) links
		linkColor = 'source-target', // source, target, source-target, or static color
		linkStrokeOpacity = 0.5, // link stroke opacity
		linkMixBlendMode = 'multiply', // link blending mode
		colors = d3.schemeTableau10, // array of colors
		width = 640, // outer width, in pixels
		height = 400, // outer height, in pixels
		marginTop = 5, // top margin, in pixels
		marginRight = 1, // right margin, in pixels
		marginBottom = 5, // bottom margin, in pixels
		marginLeft = 1, // left margin, in pixels
		onClick = undefined as ((d: any) => void) | undefined // click handler for nodes
	}: SankeyChartOptions = {}
): SVGSVGElement {
	// Convert nodeAlign from a name to a function (since d3-sankey is not part of core d3).
	if (typeof nodeAlign !== 'function') {
		nodeAlign =
			({
				left: d3Sankey.sankeyLeft,
				right: d3Sankey.sankeyRight,
				center: d3Sankey.sankeyCenter,
				justify: d3Sankey.sankeyJustify
			} as Record<string, (node: any, n: number) => number>)[nodeAlign as string] ?? d3Sankey.sankeyJustify;
	}

	// Compute values.
	const LS = d3.map(links, linkSource).map(intern);
	const LT = d3.map(links, linkTarget).map(intern);
	const LV = d3.map(links, linkValue);
	let nodesArray: InputNode[] = nodes ?? Array.from(d3.union(LS, LT), (id) => ({ id })) as any;
	const N = d3.map(nodesArray, nodeId).map(intern);
	const G = nodeGroup == null ? null : d3.map(nodesArray, nodeGroup).map(intern);

	// Replace the input nodes and links with mutable objects for the simulation.
	nodesArray = d3.map(nodesArray, (_, i) => ({ id: N[i] })) as any;
	const linksArray = d3.map(links, (_, i) => ({ source: LS[i], target: LT[i], value: LV[i] })) as any;

	// Ignore a group-based linkColor option if no groups are specified.
	if (!G && ['source', 'target', 'source-target'].includes(linkColor)) {
		linkColor = 'currentColor';
	}

	// Compute default domains.
	if (G && nodeGroups === undefined) nodeGroups = G;

	// Construct the scales.
	const color = nodeGroup == null ? null : d3.scaleOrdinal(nodeGroups, colors);

	// Compute the Sankey layout.
	d3Sankey
		.sankey()
		.nodeId(({ index: i }: any) => N[i!])
		.nodeAlign(nodeAlign as any)
		.nodeWidth(nodeWidth)
		.nodePadding(nodePadding)
		.nodeSort(nodeSort as any)
		.extent([
			[marginLeft, marginTop],
			[width - marginRight, height - marginBottom]
		])({ nodes: nodesArray as any, links: linksArray });

	// Compute titles and labels using layout nodes, so as to access aggregate values.
	if (typeof format !== 'function') format = d3.format(format);
	const Tl = nodeLabel === undefined ? N : nodeLabel == null ? null : d3.map(nodesArray, nodeLabel);
	const Tt = nodeTitle == null ? null : d3.map(nodesArray, nodeTitle);
	const Lt = linkTitle == null ? null : d3.map(linksArray, linkTitle);

	// A unique identifier for clip paths (to avoid conflicts).
	const uid = `O-${Math.random().toString(16).slice(2)}`;

	const svg = d3
		.create('svg')
		.attr('width', width)
		.attr('height', height)
		.attr('viewBox', [0, 0, width, height])
		.attr('style', 'max-width: 100%; height: auto; height: intrinsic;');

	const node = svg
		.append('g')
		.attr('stroke', nodeStroke)
		.attr('stroke-width', nodeStrokeWidth ?? null)
		.attr('stroke-opacity', nodeStrokeOpacity ?? null)
		.attr('stroke-linejoin', nodeStrokeLinejoin ?? null)
		.selectAll('rect')
		.data(nodesArray)
		.join('rect')
		.attr('x', (d: any) => d.x0)
		.attr('y', (d: any) => d.y0)
		.attr('height', (d: any) => d.y1 - d.y0)
		.attr('width', (d: any) => d.x1 - d.x0);

	if (G) node.attr('fill', ({ index: i }: any) => color!(G[i]));
	if (Tt) node.append('title').text(({ index: i }: any) => Tt[i] ?? '');
	node.on('click', (_event, d) => onClick?.(d));

	const link = svg
		.append('g')
		.attr('fill', 'none')
		.attr('stroke-opacity', linkStrokeOpacity)
		.selectAll('g')
		.data(linksArray)
		.join('g')
		.style('mix-blend-mode', linkMixBlendMode);
	link.on('click', (_event, d) => console.log(d));
	if (linkColor === 'source-target') {
		link
			.append('linearGradient')
			.attr('id', (d: any) => `${uid}-link-${d.index}`)
			.attr('gradientUnits', 'userSpaceOnUse')
			.attr('x1', (d: any) => (d.source as any).x1)
			.attr('x2', (d: any) => (d.target as any).x0)
			.call((gradient) =>
				gradient
					.append('stop')
					.attr('offset', '0%')
					.attr('stop-color', ({ source: { index: i } }: any) => color!(G![i]))
			)
			.call((gradient) =>
				gradient
					.append('stop')
					.attr('offset', '100%')
					.attr('stop-color', ({ target: { index: i } }: any) => color!(G![i]))
			);
	}

	link
		.append('path')
		.attr('d', linkPath as any)
		.attr(
			'stroke',
			linkColor === 'source-target'
				? ({ index: i }: any) => `url(#${uid}-link-${i})`
				: linkColor === 'source'
					? ({ source: { index: i } }: any) => color!(G![i])
					: linkColor === 'target'
						? ({ target: { index: i } }: any) => color!(G![i])
						: linkColor
		)
		.attr('stroke-width', ({ width }: any) => Math.max(1, width))
		.call(Lt ? (path) => path.append('title').text(({ index: i }: any) => Lt[i] ?? '') : () => {});

	if (Tl) {
		const labelGroup = svg
			.append('g')
			.attr('font-family', 'sans-serif')
			.attr('font-size', 14);

		labelGroup
			.selectAll('g')
			.data(nodesArray)
			.join('g')
			.each(function (d: any) {
				const label = Tl[d.index!];
				const labels = Array.isArray(label) ? label : [label];
				const lineHeight = 16; // spacing between lines in pixels
				const totalHeight = labels.length * lineHeight;
				const startY = (d.y1 + d.y0) / 2 - totalHeight / 2;

				d3.select(this)
					.selectAll('text')
					.data(labels)
					.join('text')
					.attr('x', d.x0 < width / 2 ? d.x1 + nodeLabelPadding : d.x0 - nodeLabelPadding)
					.attr('y', (_: any, i: number) => startY + i * lineHeight)
					.attr('dy', '0.75em')
					.attr('text-anchor', d.x0 < width / 2 ? 'start' : 'end')
					.text((labelText: string) => labelText);
			});
	}

	function intern(value: any) {
		return value !== null && typeof value === 'object' ? value.valueOf() : value;
	}

	return Object.assign(svg.node()!, { scales: { color } });
}
