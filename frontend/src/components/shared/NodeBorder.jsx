// Static decorative SVG node-and-line border pattern framing the screen edges.
// Nodes are small circles connected by thin lines in light gray (#e2e8f0).
// Purely decorative — does not animate.

const NODE_COLOR = '#e2e8f0'
const NODE_R = 3
const SPACING = 48

function buildNodes(w, h) {
  const nodes = []
  const edges = []
  let id = 0

  // Top and bottom edges
  for (let x = 0; x <= w; x += SPACING) {
    nodes.push({ id: id++, x, y: 0 })
    nodes.push({ id: id++, x, y: h })
  }
  // Left and right edges (skip corners already added)
  for (let y = SPACING; y < h; y += SPACING) {
    nodes.push({ id: id++, x: 0, y })
    nodes.push({ id: id++, x: w, y })
  }

  // Connect adjacent nodes along each edge
  const top = nodes.filter(n => n.y === 0).sort((a, b) => a.x - b.x)
  const bot = nodes.filter(n => n.y === h).sort((a, b) => a.x - b.x)
  const left = nodes.filter(n => n.x === 0).sort((a, b) => a.y - b.y)
  const right = nodes.filter(n => n.x === w).sort((a, b) => a.y - b.y)

  const addEdges = (arr) => {
    for (let i = 0; i < arr.length - 1; i++) {
      edges.push([arr[i], arr[i + 1]])
    }
  }

  addEdges(top)
  addEdges(bot)
  addEdges(left)
  addEdges(right)

  return { nodes, edges }
}

export default function NodeBorder() {
  const w = window.innerWidth
  const h = window.innerHeight
  const { nodes, edges } = buildNodes(w, h)

  return (
    <svg
      className="node-border"
      width={w}
      height={h}
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {edges.map(([a, b], i) => (
        <line
          key={i}
          x1={a.x} y1={a.y}
          x2={b.x} y2={b.y}
          stroke={NODE_COLOR}
          strokeWidth={1}
        />
      ))}
      {nodes.map(n => (
        <circle key={n.id} cx={n.x} cy={n.y} r={NODE_R} fill={NODE_COLOR} />
      ))}
    </svg>
  )
}
