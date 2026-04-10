import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface CartItem {
  product_id: number
  naam: string
  prijs: number
  aantal: number
  afbeelding_url?: string
}

interface CartStore {
  items: CartItem[]
  addItem(item: Omit<CartItem, 'aantal'>): void
  removeItem(product_id: number): void
  updateAantal(product_id: number, aantal: number): void
  clear(): void
  totaal(): number
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],

      addItem(item) {
        set((state) => {
          const existing = state.items.find((i) => i.product_id === item.product_id)
          if (existing) {
            return {
              items: state.items.map((i) =>
                i.product_id === item.product_id ? { ...i, aantal: i.aantal + 1 } : i
              ),
            }
          }
          return { items: [...state.items, { ...item, aantal: 1 }] }
        })
      },

      removeItem(product_id) {
        set((state) => ({ items: state.items.filter((i) => i.product_id !== product_id) }))
      },

      updateAantal(product_id, aantal) {
        if (aantal <= 0) {
          get().removeItem(product_id)
          return
        }
        set((state) => ({
          items: state.items.map((i) =>
            i.product_id === product_id ? { ...i, aantal } : i
          ),
        }))
      },

      clear() {
        set({ items: [] })
      },

      totaal() {
        return get().items.reduce((sum, i) => sum + i.prijs * i.aantal, 0)
      },
    }),
    { name: 'vorstersNV-cart' }
  )
)
