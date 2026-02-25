import { isTauri } from '@tauri-apps/api/core'
import { save } from '@tauri-apps/plugin-dialog'
import { writeTextFile } from '@tauri-apps/plugin-fs'
import type {
  AnalyticsEventPayload,
  ContentMatrix,
  ConsistencyCheckResult,
  ExperimentRecord,
  IdentityModelCard,
  LaunchKit,
  MonetizationMap,
  OnboardingProfile,
  PersonaConstitution,
} from '../../types/flow'

export interface DeliveryPackagePayload {
  profile?: OnboardingProfile
  primaryIdentity?: IdentityModelCard
  backupIdentity?: IdentityModelCard
  constitution?: PersonaConstitution
  launchKit?: LaunchKit
  consistencyCheck?: ConsistencyCheckResult
  contentMatrix?: ContentMatrix
  experiments?: ExperimentRecord[]
  monetizationMap?: MonetizationMap
  events: AnalyticsEventPayload[]
}

interface BrowserDownloadAnchor {
  href: string
  download: string
  click: () => void
}

export interface BrowserDownloadAdapter {
  createBlobUrl: (blob: Blob) => string
  revokeBlobUrl: (url: string) => void
  createAnchor: () => BrowserDownloadAnchor
  appendAnchor: (anchor: BrowserDownloadAnchor) => void
  removeAnchor: (anchor: BrowserDownloadAnchor) => void
}

export interface ExportDeliveryJsonOptions {
  fileName?: string
  browserAdapter?: BrowserDownloadAdapter
}

export interface ExportDeliveryJsonResult {
  status: 'saved' | 'cancelled'
  channel: 'tauri' | 'web'
  fileName: string
  filePath?: string
}

export const createDeliveryJsonFileName = (timestamp: number = Date.now()): string =>
  `bss-identity-review-${timestamp}.json`

export const serializeDeliveryPackage = (payload: DeliveryPackagePayload): string =>
  JSON.stringify(payload, null, 2)

const createDefaultBrowserAdapter = (): BrowserDownloadAdapter => ({
  createBlobUrl(blob) {
    return URL.createObjectURL(blob)
  },
  revokeBlobUrl(url) {
    URL.revokeObjectURL(url)
  },
  createAnchor() {
    return document.createElement('a')
  },
  appendAnchor(anchor) {
    document.body.appendChild(anchor as HTMLAnchorElement)
  },
  removeAnchor(anchor) {
    if ((anchor as HTMLAnchorElement).parentNode) {
      document.body.removeChild(anchor as HTMLAnchorElement)
    }
  },
})

const normalizeSelectedPath = (selectedPath: string | string[] | null): string | null => {
  if (Array.isArray(selectedPath)) {
    return selectedPath[0] ?? null
  }
  return selectedPath
}

const downloadInBrowser = (
  serializedPayload: string,
  fileName: string,
  browserAdapter: BrowserDownloadAdapter
): void => {
  const blob = new Blob([serializedPayload], { type: 'application/json' })
  const blobUrl = browserAdapter.createBlobUrl(blob)
  const anchor = browserAdapter.createAnchor()

  anchor.href = blobUrl
  anchor.download = fileName
  browserAdapter.appendAnchor(anchor)
  anchor.click()
  browserAdapter.removeAnchor(anchor)
  browserAdapter.revokeBlobUrl(blobUrl)
}

export const exportDeliveryJsonPackage = async (
  payload: DeliveryPackagePayload,
  options: ExportDeliveryJsonOptions = {}
): Promise<ExportDeliveryJsonResult> => {
  const fileName = options.fileName ?? createDeliveryJsonFileName()
  const serializedPayload = serializeDeliveryPackage(payload)

  if (isTauri()) {
    const selectedPath = normalizeSelectedPath(
      await save({
        title: 'Export JSON Delivery Package',
        defaultPath: fileName,
        filters: [
          {
            name: 'JSON',
            extensions: ['json'],
          },
        ],
      })
    )

    if (!selectedPath) {
      return {
        status: 'cancelled',
        channel: 'tauri',
        fileName,
      }
    }

    await writeTextFile(selectedPath, serializedPayload)
    return {
      status: 'saved',
      channel: 'tauri',
      fileName,
      filePath: selectedPath,
    }
  }

  const browserAdapter = options.browserAdapter ?? createDefaultBrowserAdapter()
  downloadInBrowser(serializedPayload, fileName, browserAdapter)

  return {
    status: 'saved',
    channel: 'web',
    fileName,
  }
}
