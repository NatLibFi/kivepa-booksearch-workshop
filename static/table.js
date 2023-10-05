async function generateBooksTable(reversed) {
    try {
        const response = await fetch('/searched_books');
        const data = await response.json();

        const table = $('#books-table');
        table.empty(); // Clear existing rows

        // Determine the order of the "Found in A" and "Found in B" columns based on 'reversed'
        // const reversed = true; // Set to true or false based on your logic
        // const columnOrder = reversed ? ['Found in B', 'Found in A'] : ['Found in A', 'Found in B'];
        const columnOrder = reversed ? ['Juonenjyvä', 'Tarinaluotsi'] : ['Tarinaluotsi', 'Juonenjyvä'];

        // Generate and insert the table head with the determined column order
        const tableHead = $('<thead>').html(`
            <tr>
                <th>#</th>
                <th>Nimeke</th>
                <th>Tekijä</th>
                <th>${columnOrder[0]}</th>
                <th>${columnOrder[1]}</th>
            </tr>
        `);
        table.append(tableHead);

        let rowNumber = 1; // Initialize the row number

        data.searchedBooks.forEach(book => {
            const row = $('<tr>');
            const isFoundAIcon = book.is_found_a ? '✓' : '✗';
            const isFoundBIcon = book.is_found_b ? '✓' : '✗';
            const isFoundAColor = book.is_found_a ? 'green' : 'red';
            const isFoundBColor = book.is_found_b ? 'green' : 'red';

            // Populate the row based on the determined column order
            if (reversed) {
                row.html(`
                    <td>${rowNumber}</td>
                    <td>${book.title}</td>
                    <td>${book.authors}</td>
                    <td style="color: ${isFoundBColor}; font-size: 25px; text-align: center;">${isFoundBIcon}</td>
                    <td style="color: ${isFoundAColor}; font-size: 25px; text-align: center;">${isFoundAIcon}</td>
                `);
            } else {
                row.html(`
                    <td>${rowNumber}</td>
                    <td>${book.title}</td>
                    <td>${book.authors}</td>
                    <td style="color: ${isFoundAColor}; font-size: 25px; text-align: center;">${isFoundAIcon}</td>
                    <td style="color: ${isFoundBColor}; font-size: 25px; text-align: center;">${isFoundBIcon}</td>
                `);
            }

            table.append(row);

            rowNumber++; // Increment the row number for the next row
        });
    } catch (error) {
        console.error('Error fetching selected books:', error);
    }
}
