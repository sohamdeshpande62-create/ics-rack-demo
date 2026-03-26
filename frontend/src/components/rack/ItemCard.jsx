import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'

export default function ItemCard({ item }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `card-${item.item_id}`,
    data: { item },
  })

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.4 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="item-card item-card--staging"
      {...listeners}
      {...attributes}
    >
      <span className="item-card__name">{item.name}</span>
      <span className="item-card__label">{item.label}</span>
    </div>
  )
}
