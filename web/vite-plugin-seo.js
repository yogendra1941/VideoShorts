/* Build-time SEO plugin — neutralized.

VideoShorts is now a 100% free studio app with no marketing landing, no
pricing/alternatives/FAQ SEO surface, and no cloud-vs-self-host pitch. This
plugin therefore does nothing: it no longer injects crawler marketing content
into #root and it emits no static marketing pages. The build output is the pure
React Studio SPA.

Keeping the file (instead of deleting it) keeps vite.config.js unchanged and lets
us re-enable a real, non-marketing SEO layer later (e.g. product schema) without
rewiring the build.
*/
import { loadEnv } from 'vite'

export default function seoPlugin() {
  return {
    name: 'videoshorts-seo',
    apply: 'build',
    configResolved(config) {
      loadEnv(config.mode, config.envDir, 'VITE_')
    },
    // No transform, no emitFile, no homepage injection.
  }
}
