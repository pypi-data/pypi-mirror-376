import React, {useState, useRef, useEffect} from 'react'
import {LegendConfig} from '../types'

interface LegendComponentProps {
  legendConfig: LegendConfig
  isPanePrimitive?: boolean // Flag to indicate if used as a pane primitive
}

export const LegendComponent: React.FC<LegendComponentProps> = ({
  legendConfig,
  isPanePrimitive = false
}) => {
  const [isVisible, setIsVisible] = useState(legendConfig.visible ?? true)
  const legendRef = useRef<HTMLDivElement>(null)

  // Handle visibility
  useEffect(() => {
    setIsVisible(legendConfig.visible ?? true)
  }, [legendConfig.visible])

  if (!isVisible) {
    return null
  }

  // Extract text content from HTML for accessibility
  const getTextContent = (html: string): string => {
    try {
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = html

      // Try multiple methods to extract text
      let text = tempDiv.textContent || tempDiv.innerText || ''

      // If still empty, try to clean up the HTML and extract manually
      if (!text.trim()) {
        // Remove HTML tags and extract text
        text = html.replace(/<[^>]*>/g, '').trim()
      }

      return text
    } catch (error) {
      // Fallback: return the HTML as-is if parsing fails
      return html.replace(/<[^>]*>/g, '').trim()
    }
  }

  const textContent = legendConfig.text ? getTextContent(legendConfig.text) : ''

  return (
    <div
      ref={legendRef}
      className="pane-legend"
      style={{
        // Use absolute positioning - parent (LegendPanePrimitive) handles all positioning
        position: 'absolute',
        top: 0,
        left: 0,
        zIndex: legendConfig.zIndex || 1000,
        pointerEvents: 'none',
        // Ensure it's not clipped
        overflow: 'visible'
      }}
      data-debug="legend"
    >
      {legendConfig.text ? (
        <div
          data-legend-text
          dangerouslySetInnerHTML={{__html: legendConfig.text}}
          aria-label={textContent}
          style={{
            display: 'block',
            color: legendConfig.textColor
          }}
        />
      ) : (
        <span style={{color: '#666', fontStyle: 'italic'}}>No content</span>
      )}
    </div>
  )
}
