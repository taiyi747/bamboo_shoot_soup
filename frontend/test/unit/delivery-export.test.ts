import { beforeEach, describe, expect, it, vi } from 'vitest'
import { isTauri } from '@tauri-apps/api/core'
import { save } from '@tauri-apps/plugin-dialog'
import { writeTextFile } from '@tauri-apps/plugin-fs'
import {
  exportDeliveryJsonPackage,
  type BrowserDownloadAdapter,
  type DeliveryPackagePayload,
} from '../../app/services/export/delivery'

vi.mock('@tauri-apps/api/core', () => ({
  isTauri: vi.fn(),
}))

vi.mock('@tauri-apps/plugin-dialog', () => ({
  save: vi.fn(),
}))

vi.mock('@tauri-apps/plugin-fs', () => ({
  writeTextFile: vi.fn(),
}))

const basePayload: DeliveryPackagePayload = {
  events: [],
}

describe('exportDeliveryJsonPackage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('writes json file when running in tauri and path is selected', async () => {
    vi.mocked(isTauri).mockReturnValue(true)
    vi.mocked(save).mockResolvedValue('C:/tmp/review.json')
    vi.mocked(writeTextFile).mockResolvedValue()

    const result = await exportDeliveryJsonPackage(basePayload, { fileName: 'review.json' })

    expect(save).toHaveBeenCalledWith(
      expect.objectContaining({
        defaultPath: 'review.json',
      })
    )
    expect(writeTextFile).toHaveBeenCalledTimes(1)
    const [writtenPath, writtenPayload] = vi.mocked(writeTextFile).mock.calls[0]
    expect(writtenPath).toBe('C:/tmp/review.json')
    expect(writtenPayload).toContain('"events": []')
    expect(writtenPayload).toContain('"schema_version": "1.1.0"')
    expect(result).toEqual({
      status: 'saved',
      channel: 'tauri',
      fileName: 'review.json',
      filePath: 'C:/tmp/review.json',
    })
  })

  it('returns cancelled when tauri save dialog is dismissed', async () => {
    vi.mocked(isTauri).mockReturnValue(true)
    vi.mocked(save).mockResolvedValue(null)

    const result = await exportDeliveryJsonPackage(basePayload, { fileName: 'review.json' })

    expect(writeTextFile).not.toHaveBeenCalled()
    expect(result).toEqual({
      status: 'cancelled',
      channel: 'tauri',
      fileName: 'review.json',
    })
  })

  it('falls back to browser download when not running in tauri', async () => {
    vi.mocked(isTauri).mockReturnValue(false)

    const clickSpy = vi.fn()
    const anchor = { href: '', download: '', click: clickSpy }
    const createBlobUrl = vi.fn(() => 'blob:review')
    const revokeBlobUrl = vi.fn()
    const appendAnchor = vi.fn()
    const removeAnchor = vi.fn()

    const browserAdapter: BrowserDownloadAdapter = {
      createBlobUrl,
      revokeBlobUrl,
      createAnchor: () => anchor,
      appendAnchor,
      removeAnchor,
    }

    const result = await exportDeliveryJsonPackage(basePayload, {
      fileName: 'review.json',
      browserAdapter,
    })

    expect(createBlobUrl).toHaveBeenCalledTimes(1)
    expect(anchor.download).toBe('review.json')
    expect(anchor.href).toBe('blob:review')
    expect(appendAnchor).toHaveBeenCalledWith(anchor)
    expect(clickSpy).toHaveBeenCalledTimes(1)
    expect(removeAnchor).toHaveBeenCalledWith(anchor)
    expect(revokeBlobUrl).toHaveBeenCalledWith('blob:review')
    expect(writeTextFile).not.toHaveBeenCalled()
    expect(result).toEqual({
      status: 'saved',
      channel: 'web',
      fileName: 'review.json',
    })
  })

  it('throws when tauri file write fails', async () => {
    vi.mocked(isTauri).mockReturnValue(true)
    vi.mocked(save).mockResolvedValue('C:/tmp/review.json')
    vi.mocked(writeTextFile).mockRejectedValue(new Error('write failed'))

    await expect(exportDeliveryJsonPackage(basePayload, { fileName: 'review.json' })).rejects.toThrow('write failed')
  })
})
