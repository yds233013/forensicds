# Courier supply — scheduling note

Couriers choose their own hours. They are not rostered. The scheduling team reviews online hours weekly and
has consistently found that online hours in a market track **expected earnings per online hour** in that
market over the preceding days: couriers come online where the week has been paying, and stop early where it
has not.

Couriers see the guarantee as a property of the market they are working, not of an individual offer — the
in-app earnings summary reports realised earnings per hour for the week to date, by market.

Online hours per courier per clock hour are in `courier_shifts`. Nothing in the platform caps the number of
couriers who may be online in a market-hour.

A denser pool of available couriers shortens the distance from the accepting courier to the pickup point.
The dispatch radius is unchanged by Boost.
