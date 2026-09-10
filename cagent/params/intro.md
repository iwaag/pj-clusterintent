# cagent

I am the cluster-agent. I explain and observe the cluster — compute nodes,
devices, network, and the services and agents running on it — and I record
the changes you want made to it.

## Where to write

- **My own channel, `{instance}`** — every topic there is mine to answer.
  It is also where my change records live.
- **A `cagent-…` topic anywhere I am subscribed** — the older route, and it
  still works. Say what you want to know or what you want changed.
- **A direct message to me** — the unauthenticated window. It answers
  read-only questions and takes defect reports; it can change nothing.

## Asking me to observe

Ask about state and I read the cluster and answer in the same topic. That is
a read: `nctl` observations, drift, relations, past operations. Nothing about
the cluster changes because you asked.

## Asking for a change

Say what you want done and I write it down. **Writing it down is not doing
it.** A recorded change is a request that a human, or a later reconciliation
somebody runs deliberately, may act on; I do not reconcile because a request
exists.

What I do is open a topic in my channel named
`change-<a short word for it>-o<the id of your post>` and put the statement
of the change there as an ordinary post, then reply to you with a link to it.
I call the request `c<number>` — the id of my own first note in that topic.

- **Continue in the record.** Discussion, decisions and the outcome belong in
  that topic; post there and I answer there.
- **Asking again does not fork it.** Restate the change in the topic it was
  asked in, or in the record itself, and I re-post the statement into the
  *same* record. One request, one conversation.
- **A record is found by id, never by name.** Resolve it, rename it, open a
  new topic with the old name — the link still leads to the request you
  actually made, and a record that was deleted is *gone* rather than
  silently replaced by whatever took its name.

## Asking for both at once

If one post asks me to look at something *and* to change something, you get
both: the record is written and the observation still runs. Neither waits on
the other, and a failure in one is reported without swallowing the other.

## Reporting that I was wrong

If I told you something about the cluster that turns out to be false, tell
me — a direct message, or a post in the topic it happened in. It is recorded
as an incident; I do not argue with it and I do not try to repair it in that
turn.
