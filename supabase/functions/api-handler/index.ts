import { withSupabase } from 'npm:@supabase/server'

/**
 * Example Supabase Edge Function using @supabase/server
 * Handlers are automatically injected with typed Supabase context and auth modes.
 *
 * Supported auth modes: 'user' | 'publishable' | 'secret' | 'none'
 */

export default {
  fetch: withSupabase({ auth: 'user' }, async (_req, ctx) => {
    // Authenticated user context is available on ctx.supabase
    const { data, error } = await ctx.supabase.from('projects').select('*')

    if (error) {
      return Response.json({ error: error.message }, { status: 400 })
    }

    return Response.json({
      success: true,
      authMode: ctx.authMode,
      user: ctx.user,
      data,
    })
  }),
}
