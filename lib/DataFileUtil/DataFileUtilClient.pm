package DataFileUtil::DataFileUtilClient;

use JSON::RPC::Client;
use POSIX;
use strict;
use Data::Dumper;
use URI;
use Bio::KBase::Exceptions;
my $get_time = sub { time, 0 };
eval {
    require Time::HiRes;
    $get_time = sub { Time::HiRes::gettimeofday() };
};

use Bio::KBase::AuthToken;

# Client version should match Impl version
# This is a Semantic Version number,
# http://semver.org
our $VERSION = "0.1.0";

=head1 NAME

DataFileUtil::DataFileUtilClient

=head1 DESCRIPTION


Contains utilities for saving and retrieving data to and from KBase data
services. Requires Shock 0.9.6+ and Workspace Service 0.4.1+.


=cut

sub new
{
    my($class, $url, @args) = @_;
    

    my $self = {
	client => DataFileUtil::DataFileUtilClient::RpcClient->new,
	url => $url,
	headers => [],
    };

    chomp($self->{hostname} = `hostname`);
    $self->{hostname} ||= 'unknown-host';

    #
    # Set up for propagating KBRPC_TAG and KBRPC_METADATA environment variables through
    # to invoked services. If these values are not set, we create a new tag
    # and a metadata field with basic information about the invoking script.
    #
    if ($ENV{KBRPC_TAG})
    {
	$self->{kbrpc_tag} = $ENV{KBRPC_TAG};
    }
    else
    {
	my ($t, $us) = &$get_time();
	$us = sprintf("%06d", $us);
	my $ts = strftime("%Y-%m-%dT%H:%M:%S.${us}Z", gmtime $t);
	$self->{kbrpc_tag} = "C:$0:$self->{hostname}:$$:$ts";
    }
    push(@{$self->{headers}}, 'Kbrpc-Tag', $self->{kbrpc_tag});

    if ($ENV{KBRPC_METADATA})
    {
	$self->{kbrpc_metadata} = $ENV{KBRPC_METADATA};
	push(@{$self->{headers}}, 'Kbrpc-Metadata', $self->{kbrpc_metadata});
    }

    if ($ENV{KBRPC_ERROR_DEST})
    {
	$self->{kbrpc_error_dest} = $ENV{KBRPC_ERROR_DEST};
	push(@{$self->{headers}}, 'Kbrpc-Errordest', $self->{kbrpc_error_dest});
    }

    #
    # This module requires authentication.
    #
    # We create an auth token, passing through the arguments that we were (hopefully) given.

    {
	my $token = Bio::KBase::AuthToken->new(@args);
	
	if (!$token->error_message)
	{
	    $self->{token} = $token->token;
	    $self->{client}->{token} = $token->token;
	}
        else
        {
	    #
	    # All methods in this module require authentication. In this case, if we
	    # don't have a token, we can't continue.
	    #
	    die "Authentication failed: " . $token->error_message;
	}
    }

    my $ua = $self->{client}->ua;	 
    my $timeout = $ENV{CDMI_TIMEOUT} || (30 * 60);	 
    $ua->timeout($timeout);
    bless $self, $class;
    #    $self->_validate_version();
    return $self;
}




=head2 shock_to_file

  $out = $obj->shock_to_file($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.ShockToFileParams
$out is a DataFileUtil.ShockToFileOutput
ShockToFileParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	file_path has a value which is a string
	unpack has a value which is a string
ShockToFileOutput is a reference to a hash where the following keys are defined:
	node_file_name has a value which is a string
	file_path has a value which is a string
	size has a value which is an int
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object

</pre>

=end html

=begin text

$params is a DataFileUtil.ShockToFileParams
$out is a DataFileUtil.ShockToFileOutput
ShockToFileParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	file_path has a value which is a string
	unpack has a value which is a string
ShockToFileOutput is a reference to a hash where the following keys are defined:
	node_file_name has a value which is a string
	file_path has a value which is a string
	size has a value which is an int
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object


=end text

=item Description

Download a file from Shock.

=back

=cut

 sub shock_to_file
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function shock_to_file (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to shock_to_file:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'shock_to_file');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.shock_to_file",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'shock_to_file',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method shock_to_file",
					    status_line => $self->{client}->status_line,
					    method_name => 'shock_to_file',
				       );
    }
}
 


=head2 shock_to_file_mass

  $out = $obj->shock_to_file_mass($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a reference to a list where each element is a DataFileUtil.ShockToFileParams
$out is a reference to a list where each element is a DataFileUtil.ShockToFileOutput
ShockToFileParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	file_path has a value which is a string
	unpack has a value which is a string
ShockToFileOutput is a reference to a hash where the following keys are defined:
	node_file_name has a value which is a string
	file_path has a value which is a string
	size has a value which is an int
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object

</pre>

=end html

=begin text

$params is a reference to a list where each element is a DataFileUtil.ShockToFileParams
$out is a reference to a list where each element is a DataFileUtil.ShockToFileOutput
ShockToFileParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	file_path has a value which is a string
	unpack has a value which is a string
ShockToFileOutput is a reference to a hash where the following keys are defined:
	node_file_name has a value which is a string
	file_path has a value which is a string
	size has a value which is an int
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object


=end text

=item Description

Download multiple files from Shock.

=back

=cut

 sub shock_to_file_mass
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function shock_to_file_mass (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'ARRAY') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to shock_to_file_mass:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'shock_to_file_mass');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.shock_to_file_mass",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'shock_to_file_mass',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method shock_to_file_mass",
					    status_line => $self->{client}->status_line,
					    method_name => 'shock_to_file_mass',
				       );
    }
}
 


=head2 file_to_shock

  $out = $obj->file_to_shock($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.FileToShockParams
$out is a DataFileUtil.FileToShockOutput
FileToShockParams is a reference to a hash where the following keys are defined:
	file_path has a value which is a string
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
	make_handle has a value which is a DataFileUtil.boolean
	pack has a value which is a string
boolean is an int
FileToShockOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle has a value which is a DataFileUtil.Handle
	node_file_name has a value which is a string
	size has a value which is a string
Handle is a reference to a hash where the following keys are defined:
	hid has a value which is a string
	file_name has a value which is a string
	id has a value which is a string
	url has a value which is a string
	type has a value which is a string
	remote_md5 has a value which is a string

</pre>

=end html

=begin text

$params is a DataFileUtil.FileToShockParams
$out is a DataFileUtil.FileToShockOutput
FileToShockParams is a reference to a hash where the following keys are defined:
	file_path has a value which is a string
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
	make_handle has a value which is a DataFileUtil.boolean
	pack has a value which is a string
boolean is an int
FileToShockOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle has a value which is a DataFileUtil.Handle
	node_file_name has a value which is a string
	size has a value which is a string
Handle is a reference to a hash where the following keys are defined:
	hid has a value which is a string
	file_name has a value which is a string
	id has a value which is a string
	url has a value which is a string
	type has a value which is a string
	remote_md5 has a value which is a string


=end text

=item Description

Load a file to Shock.

=back

=cut

 sub file_to_shock
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function file_to_shock (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to file_to_shock:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'file_to_shock');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.file_to_shock",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'file_to_shock',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method file_to_shock",
					    status_line => $self->{client}->status_line,
					    method_name => 'file_to_shock',
				       );
    }
}
 


=head2 file_to_shock_mass

  $out = $obj->file_to_shock_mass($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a reference to a list where each element is a DataFileUtil.FileToShockParams
$out is a reference to a list where each element is a DataFileUtil.FileToShockOutput
FileToShockParams is a reference to a hash where the following keys are defined:
	file_path has a value which is a string
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
	make_handle has a value which is a DataFileUtil.boolean
	pack has a value which is a string
boolean is an int
FileToShockOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle has a value which is a DataFileUtil.Handle
	node_file_name has a value which is a string
	size has a value which is a string
Handle is a reference to a hash where the following keys are defined:
	hid has a value which is a string
	file_name has a value which is a string
	id has a value which is a string
	url has a value which is a string
	type has a value which is a string
	remote_md5 has a value which is a string

</pre>

=end html

=begin text

$params is a reference to a list where each element is a DataFileUtil.FileToShockParams
$out is a reference to a list where each element is a DataFileUtil.FileToShockOutput
FileToShockParams is a reference to a hash where the following keys are defined:
	file_path has a value which is a string
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
	make_handle has a value which is a DataFileUtil.boolean
	pack has a value which is a string
boolean is an int
FileToShockOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle has a value which is a DataFileUtil.Handle
	node_file_name has a value which is a string
	size has a value which is a string
Handle is a reference to a hash where the following keys are defined:
	hid has a value which is a string
	file_name has a value which is a string
	id has a value which is a string
	url has a value which is a string
	type has a value which is a string
	remote_md5 has a value which is a string


=end text

=item Description

Load multiple files to Shock.

=back

=cut

 sub file_to_shock_mass
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function file_to_shock_mass (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'ARRAY') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to file_to_shock_mass:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'file_to_shock_mass');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.file_to_shock_mass",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'file_to_shock_mass',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method file_to_shock_mass",
					    status_line => $self->{client}->status_line,
					    method_name => 'file_to_shock_mass',
				       );
    }
}
 


=head2 copy_shock_node

  $out = $obj->copy_shock_node($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.CopyShockNodeParams
$out is a DataFileUtil.CopyShockNodeOutput
CopyShockNodeParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	make_handle has a value which is a DataFileUtil.boolean
boolean is an int
CopyShockNodeOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle has a value which is a DataFileUtil.Handle
Handle is a reference to a hash where the following keys are defined:
	hid has a value which is a string
	file_name has a value which is a string
	id has a value which is a string
	url has a value which is a string
	type has a value which is a string
	remote_md5 has a value which is a string

</pre>

=end html

=begin text

$params is a DataFileUtil.CopyShockNodeParams
$out is a DataFileUtil.CopyShockNodeOutput
CopyShockNodeParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	make_handle has a value which is a DataFileUtil.boolean
boolean is an int
CopyShockNodeOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle has a value which is a DataFileUtil.Handle
Handle is a reference to a hash where the following keys are defined:
	hid has a value which is a string
	file_name has a value which is a string
	id has a value which is a string
	url has a value which is a string
	type has a value which is a string
	remote_md5 has a value which is a string


=end text

=item Description

Copy a Shock node.

=back

=cut

 sub copy_shock_node
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function copy_shock_node (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to copy_shock_node:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'copy_shock_node');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.copy_shock_node",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'copy_shock_node',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method copy_shock_node",
					    status_line => $self->{client}->status_line,
					    method_name => 'copy_shock_node',
				       );
    }
}
 


=head2 own_shock_node

  $out = $obj->own_shock_node($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.OwnShockNodeParams
$out is a DataFileUtil.OwnShockNodeOutput
OwnShockNodeParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	make_handle has a value which is a DataFileUtil.boolean
boolean is an int
OwnShockNodeOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle has a value which is a DataFileUtil.Handle
Handle is a reference to a hash where the following keys are defined:
	hid has a value which is a string
	file_name has a value which is a string
	id has a value which is a string
	url has a value which is a string
	type has a value which is a string
	remote_md5 has a value which is a string

</pre>

=end html

=begin text

$params is a DataFileUtil.OwnShockNodeParams
$out is a DataFileUtil.OwnShockNodeOutput
OwnShockNodeParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	make_handle has a value which is a DataFileUtil.boolean
boolean is an int
OwnShockNodeOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle has a value which is a DataFileUtil.Handle
Handle is a reference to a hash where the following keys are defined:
	hid has a value which is a string
	file_name has a value which is a string
	id has a value which is a string
	url has a value which is a string
	type has a value which is a string
	remote_md5 has a value which is a string


=end text

=item Description

Gain ownership of a Shock node.

Returns a shock node id which is owned by the caller, given a shock
node id.

If the shock node is already owned by the caller, returns the same
shock node ID. If not, the ID of a copy of the original node will be
returned.

If a handle is requested, the node is already owned by the caller, and
a handle already exists, that handle will be returned. Otherwise a new
handle will be created and returned.

=back

=cut

 sub own_shock_node
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function own_shock_node (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to own_shock_node:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'own_shock_node');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.own_shock_node",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'own_shock_node',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method own_shock_node",
					    status_line => $self->{client}->status_line,
					    method_name => 'own_shock_node',
				       );
    }
}
 


=head2 ws_name_to_id

  $id = $obj->ws_name_to_id($name)

=over 4

=item Parameter and return types

=begin html

<pre>
$name is a string
$id is an int

</pre>

=end html

=begin text

$name is a string
$id is an int


=end text

=item Description

Translate a workspace name to a workspace ID.

=back

=cut

 sub ws_name_to_id
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function ws_name_to_id (received $n, expecting 1)");
    }
    {
	my($name) = @args;

	my @_bad_arguments;
        (!ref($name)) or push(@_bad_arguments, "Invalid type for argument 1 \"name\" (value was \"$name\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to ws_name_to_id:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'ws_name_to_id');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.ws_name_to_id",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'ws_name_to_id',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method ws_name_to_id",
					    status_line => $self->{client}->status_line,
					    method_name => 'ws_name_to_id',
				       );
    }
}
 


=head2 save_objects

  $info = $obj->save_objects($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.SaveObjectsParams
$info is a reference to a list where each element is a DataFileUtil.object_info
SaveObjectsParams is a reference to a hash where the following keys are defined:
	id has a value which is an int
	objects has a value which is a reference to a list where each element is a DataFileUtil.ObjectSaveData
ObjectSaveData is a reference to a hash where the following keys are defined:
	type has a value which is a string
	data has a value which is an UnspecifiedObject, which can hold any non-null object
	name has a value which is a string
	objid has a value which is an int
	meta has a value which is a reference to a hash where the key is a string and the value is a string
	hidden has a value which is a DataFileUtil.boolean
boolean is an int
object_info is a reference to a list containing 11 items:
	0: (objid) an int
	1: (name) a string
	2: (type) a string
	3: (save_date) a string
	4: (version) an int
	5: (saved_by) a string
	6: (wsid) an int
	7: (workspace) a string
	8: (chsum) a string
	9: (size) an int
	10: (meta) a reference to a hash where the key is a string and the value is a string

</pre>

=end html

=begin text

$params is a DataFileUtil.SaveObjectsParams
$info is a reference to a list where each element is a DataFileUtil.object_info
SaveObjectsParams is a reference to a hash where the following keys are defined:
	id has a value which is an int
	objects has a value which is a reference to a list where each element is a DataFileUtil.ObjectSaveData
ObjectSaveData is a reference to a hash where the following keys are defined:
	type has a value which is a string
	data has a value which is an UnspecifiedObject, which can hold any non-null object
	name has a value which is a string
	objid has a value which is an int
	meta has a value which is a reference to a hash where the key is a string and the value is a string
	hidden has a value which is a DataFileUtil.boolean
boolean is an int
object_info is a reference to a list containing 11 items:
	0: (objid) an int
	1: (name) a string
	2: (type) a string
	3: (save_date) a string
	4: (version) an int
	5: (saved_by) a string
	6: (wsid) an int
	7: (workspace) a string
	8: (chsum) a string
	9: (size) an int
	10: (meta) a reference to a hash where the key is a string and the value is a string


=end text

=item Description

Save objects to the workspace. Saving over a deleted object undeletes
it.

=back

=cut

 sub save_objects
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function save_objects (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to save_objects:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'save_objects');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.save_objects",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'save_objects',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method save_objects",
					    status_line => $self->{client}->status_line,
					    method_name => 'save_objects',
				       );
    }
}
 


=head2 get_objects

  $results = $obj->get_objects($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.GetObjectsParams
$results is a DataFileUtil.GetObjectsResults
GetObjectsParams is a reference to a hash where the following keys are defined:
	object_refs has a value which is a reference to a list where each element is a string
	ignore_errors has a value which is a DataFileUtil.boolean
boolean is an int
GetObjectsResults is a reference to a hash where the following keys are defined:
	data has a value which is a reference to a list where each element is a DataFileUtil.ObjectData
ObjectData is a reference to a hash where the following keys are defined:
	data has a value which is an UnspecifiedObject, which can hold any non-null object
	info has a value which is a DataFileUtil.object_info
object_info is a reference to a list containing 11 items:
	0: (objid) an int
	1: (name) a string
	2: (type) a string
	3: (save_date) a string
	4: (version) an int
	5: (saved_by) a string
	6: (wsid) an int
	7: (workspace) a string
	8: (chsum) a string
	9: (size) an int
	10: (meta) a reference to a hash where the key is a string and the value is a string

</pre>

=end html

=begin text

$params is a DataFileUtil.GetObjectsParams
$results is a DataFileUtil.GetObjectsResults
GetObjectsParams is a reference to a hash where the following keys are defined:
	object_refs has a value which is a reference to a list where each element is a string
	ignore_errors has a value which is a DataFileUtil.boolean
boolean is an int
GetObjectsResults is a reference to a hash where the following keys are defined:
	data has a value which is a reference to a list where each element is a DataFileUtil.ObjectData
ObjectData is a reference to a hash where the following keys are defined:
	data has a value which is an UnspecifiedObject, which can hold any non-null object
	info has a value which is a DataFileUtil.object_info
object_info is a reference to a list containing 11 items:
	0: (objid) an int
	1: (name) a string
	2: (type) a string
	3: (save_date) a string
	4: (version) an int
	5: (saved_by) a string
	6: (wsid) an int
	7: (workspace) a string
	8: (chsum) a string
	9: (size) an int
	10: (meta) a reference to a hash where the key is a string and the value is a string


=end text

=item Description

Get objects from the workspace.

=back

=cut

 sub get_objects
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function get_objects (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to get_objects:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'get_objects');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.get_objects",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'get_objects',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method get_objects",
					    status_line => $self->{client}->status_line,
					    method_name => 'get_objects',
				       );
    }
}
 


=head2 versions

  $wsver, $shockver = $obj->versions()

=over 4

=item Parameter and return types

=begin html

<pre>
$wsver is a string
$shockver is a string

</pre>

=end html

=begin text

$wsver is a string
$shockver is a string


=end text

=item Description

Get the versions of the Workspace service and Shock service.

=back

=cut

 sub versions
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 0)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function versions (received $n, expecting 0)");
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.versions",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'versions',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method versions",
					    status_line => $self->{client}->status_line,
					    method_name => 'versions',
				       );
    }
}
 
  
sub status
{
    my($self, @args) = @_;
    if ((my $n = @args) != 0) {
        Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
                                   "Invalid argument count for function status (received $n, expecting 0)");
    }
    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
        method => "DataFileUtil.status",
        params => \@args,
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
                           code => $result->content->{error}->{code},
                           method_name => 'status',
                           data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
                          );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method status",
                        status_line => $self->{client}->status_line,
                        method_name => 'status',
                       );
    }
}
   

sub version {
    my ($self) = @_;
    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
        method => "DataFileUtil.version",
        params => [],
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(
                error => $result->error_message,
                code => $result->content->{code},
                method_name => 'versions',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method versions",
            status_line => $self->{client}->status_line,
            method_name => 'versions',
        );
    }
}

sub _validate_version {
    my ($self) = @_;
    my $svr_version = $self->version();
    my $client_version = $VERSION;
    my ($cMajor, $cMinor) = split(/\./, $client_version);
    my ($sMajor, $sMinor) = split(/\./, $svr_version);
    if ($sMajor != $cMajor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Major version numbers differ.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor < $cMinor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Client minor version greater than Server minor version.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor > $cMinor) {
        warn "New client version available for DataFileUtil::DataFileUtilClient\n";
    }
    if ($sMajor == 0) {
        warn "DataFileUtil::DataFileUtilClient version is $svr_version. API subject to change.\n";
    }
}

=head1 TYPES



=head2 boolean

=over 4



=item Description

A boolean - 0 for false, 1 for true.
@range (0, 1)


=item Definition

=begin html

<pre>
an int
</pre>

=end html

=begin text

an int

=end text

=back



=head2 Handle

=over 4



=item Description

A handle for a file stored in Shock.
hid - the id of the handle in the Handle Service that references this
   shock node
id - the id for the shock node
url - the url of the shock server
type - the type of the handle. This should always be shock.
file_name - the name of the file
remote_md5 - the md5 digest of the file.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
hid has a value which is a string
file_name has a value which is a string
id has a value which is a string
url has a value which is a string
type has a value which is a string
remote_md5 has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
hid has a value which is a string
file_name has a value which is a string
id has a value which is a string
url has a value which is a string
type has a value which is a string
remote_md5 has a value which is a string


=end text

=back



=head2 ShockToFileParams

=over 4



=item Description

Input for the shock_to_file function.

Required parameters:
shock_id - the ID of the Shock node.
file_path - the location to save the file output. If this is a
    directory, the file will be named as per the filename in Shock.

Optional parameters:
unpack - either null, 'uncompress', or 'unpack'. 'uncompress' will cause
    any bzip or gzip files to be uncompressed. 'unpack' will behave the
    same way, but it will also unpack tar and zip archive files
    (uncompressing gzipped or bzipped archive files if necessary). If
    'uncompress' is specified and an archive file is encountered, an
    error will be thrown. If the file is an archive, it will be
    unbundled into the directory containing the original output file.
    
    Note that if the file name (either as provided by the user or by
    Shock) without the a decompression extension (e.g. .gz, .zip or
    .tgz -> .tar) points to an existing file and unpack is specified,
    that file will be overwritten by the decompressed Shock file.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
file_path has a value which is a string
unpack has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
file_path has a value which is a string
unpack has a value which is a string


=end text

=back



=head2 ShockToFileOutput

=over 4



=item Description

Output from the shock_to_file function.

   node_file_name - the filename of the file as stored in Shock.
   file_path - the path to the downloaded file. If a directory was
       specified in the input, this will be the directory appended with the
       shock file name. If a file was specified, it will be that file path.
       In either case, if the file is uncompressed any compression file
       extensions will be removed (e.g. .gz) and or altered (e.g. .tgz ->
       .tar) as appropriate.
   size - the size of the file in bytes as stored in Shock, prior to
       unpacking.
   attributes - the file attributes, if any, stored in Shock.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
node_file_name has a value which is a string
file_path has a value which is a string
size has a value which is an int
attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
node_file_name has a value which is a string
file_path has a value which is a string
size has a value which is an int
attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object


=end text

=back



=head2 FileToShockParams

=over 4



=item Description

Input for the file_to_shock function.

Required parameters:
file_path - the location of the file to load to Shock.

Optional parameters:
attributes - user-specified attributes to save to the Shock node along
    with the file.
make_handle - make a Handle Service handle for the shock node. Default
    false.
pack - compress a file or archive a directory before loading to Shock.
    The file_path argument will be appended with the appropriate file
    extension prior to writing. For gzips only, if the file extension
    denotes that the file is already compressed, it will be skipped. If
    file_path is a directory and tarring or zipping is specified, the
    created file name will be set to the directory name, possibly
    overwriting an existing file. Attempting to pack the root directory
    is an error.
    
    The allowed values are:
        gzip - gzip the file given by file_path.
        targz - tar and gzip the directory specified by the directory
            portion of the file_path into the file specified by the
            file_path.
        zip - as targz but zip the directory.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
file_path has a value which is a string
attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
make_handle has a value which is a DataFileUtil.boolean
pack has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
file_path has a value which is a string
attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
make_handle has a value which is a DataFileUtil.boolean
pack has a value which is a string


=end text

=back



=head2 FileToShockOutput

=over 4



=item Description

Output of the file_to_shock function.

    shock_id - the ID of the new Shock node.
    handle - the new handle, if created. Null otherwise.
    node_file_name - the name of the file stored in Shock.
    size - the size of the file stored in shock.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
handle has a value which is a DataFileUtil.Handle
node_file_name has a value which is a string
size has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
handle has a value which is a DataFileUtil.Handle
node_file_name has a value which is a string
size has a value which is a string


=end text

=back



=head2 CopyShockNodeParams

=over 4



=item Description

Input for the copy_shock_node function.

       Required parameters:
       shock_id - the id of the node to copy.
       
       Optional parameters:
       make_handle - make a Handle Service handle for the shock node. Default
           false.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
make_handle has a value which is a DataFileUtil.boolean

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
make_handle has a value which is a DataFileUtil.boolean


=end text

=back



=head2 CopyShockNodeOutput

=over 4



=item Description

Output of the copy_shock_node function.

 shock_id - the id of the new Shock node.
 handle - the new handle, if created. Null otherwise.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
handle has a value which is a DataFileUtil.Handle

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
handle has a value which is a DataFileUtil.Handle


=end text

=back



=head2 OwnShockNodeParams

=over 4



=item Description

Input for the own_shock_node function.

       Required parameters:
       shock_id - the id of the node for which the user needs ownership.
       
       Optional parameters:
       make_handle - make or find a Handle Service handle for the shock node.
           Default false.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
make_handle has a value which is a DataFileUtil.boolean

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
make_handle has a value which is a DataFileUtil.boolean


=end text

=back



=head2 OwnShockNodeOutput

=over 4



=item Description

Output of the own_shock_node function.

 shock_id - the id of the (possibly new) Shock node.
 handle - the handle, if requested. Null otherwise.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
handle has a value which is a DataFileUtil.Handle

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
handle has a value which is a DataFileUtil.Handle


=end text

=back



=head2 object_info

=over 4



=item Description

Information about an object, including user provided metadata.

    objid - the numerical id of the object.
    name - the name of the object.
    type - the type of the object.
    save_date - the save date of the object.
    ver - the version of the object.
    saved_by - the user that saved or copied the object.
    wsid - the id of the workspace containing the object.
    workspace - the name of the workspace containing the object.
    chsum - the md5 checksum of the object.
    size - the size of the object in bytes.
    meta - arbitrary user-supplied metadata about
        the object.


=item Definition

=begin html

<pre>
a reference to a list containing 11 items:
0: (objid) an int
1: (name) a string
2: (type) a string
3: (save_date) a string
4: (version) an int
5: (saved_by) a string
6: (wsid) an int
7: (workspace) a string
8: (chsum) a string
9: (size) an int
10: (meta) a reference to a hash where the key is a string and the value is a string

</pre>

=end html

=begin text

a reference to a list containing 11 items:
0: (objid) an int
1: (name) a string
2: (type) a string
3: (save_date) a string
4: (version) an int
5: (saved_by) a string
6: (wsid) an int
7: (workspace) a string
8: (chsum) a string
9: (size) an int
10: (meta) a reference to a hash where the key is a string and the value is a string


=end text

=back



=head2 ObjectSaveData

=over 4



=item Description

An object and associated data required for saving.

    Required parameters:
    type - the workspace type string for the object. Omit the version
        information to use the latest version.
    data - the object data.
    
    Optional parameters:
    One of an object name or id. If no name or id is provided the name
        will be set to 'auto' with the object id appended as a string,
        possibly with -\d+ appended if that object id already exists as a
        name.
    name - the name of the object.
    objid - the id of the object to save over.
    meta - arbitrary user-supplied metadata for the object,
        not to exceed 16kb; if the object type specifies automatic
        metadata extraction with the 'meta ws' annotation, and your
        metadata name conflicts, then your metadata will be silently
        overwritten.
    hidden - true if this object should not be listed when listing
        workspace objects.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
type has a value which is a string
data has a value which is an UnspecifiedObject, which can hold any non-null object
name has a value which is a string
objid has a value which is an int
meta has a value which is a reference to a hash where the key is a string and the value is a string
hidden has a value which is a DataFileUtil.boolean

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
type has a value which is a string
data has a value which is an UnspecifiedObject, which can hold any non-null object
name has a value which is a string
objid has a value which is an int
meta has a value which is a reference to a hash where the key is a string and the value is a string
hidden has a value which is a DataFileUtil.boolean


=end text

=back



=head2 SaveObjectsParams

=over 4



=item Description

Input parameters for the "save_objects" function.

    Required parameters:
    id - the numerical ID of the workspace.
    objects - the objects to save.
    
    The object provenance is automatically pulled from the SDK runner.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
id has a value which is an int
objects has a value which is a reference to a list where each element is a DataFileUtil.ObjectSaveData

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
id has a value which is an int
objects has a value which is a reference to a list where each element is a DataFileUtil.ObjectSaveData


=end text

=back



=head2 GetObjectsParams

=over 4



=item Description

Input parameters for the "get_objects" function.

    Required parameters:
    object_refs - a list of object references in the form X/Y/Z, where X is
        the workspace name or id, Y is the object name or id, and Z is the
        (optional) object version. In general, always use ids rather than
        names if possible to avoid race conditions.
    
    Optional parameters:
    ignore_errors - ignore any errors that occur when fetching an object
        and instead insert a null into the returned list.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
object_refs has a value which is a reference to a list where each element is a string
ignore_errors has a value which is a DataFileUtil.boolean

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
object_refs has a value which is a reference to a list where each element is a string
ignore_errors has a value which is a DataFileUtil.boolean


=end text

=back



=head2 ObjectData

=over 4



=item Description

The data and supplemental info for an object.

    UnspecifiedObject data - the object's data or subset data.
    object_info info - information about the object.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
data has a value which is an UnspecifiedObject, which can hold any non-null object
info has a value which is a DataFileUtil.object_info

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
data has a value which is an UnspecifiedObject, which can hold any non-null object
info has a value which is a DataFileUtil.object_info


=end text

=back



=head2 GetObjectsResults

=over 4



=item Description

Results from the get_objects function.

    list<ObjectData> data - the returned objects.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
data has a value which is a reference to a list where each element is a DataFileUtil.ObjectData

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
data has a value which is a reference to a list where each element is a DataFileUtil.ObjectData


=end text

=back



=cut

package DataFileUtil::DataFileUtilClient::RpcClient;
use base 'JSON::RPC::Client';
use POSIX;
use strict;

#
# Override JSON::RPC::Client::call because it doesn't handle error returns properly.
#

sub call {
    my ($self, $uri, $headers, $obj) = @_;
    my $result;


    {
	if ($uri =~ /\?/) {
	    $result = $self->_get($uri);
	}
	else {
	    Carp::croak "not hashref." unless (ref $obj eq 'HASH');
	    $result = $self->_post($uri, $headers, $obj);
	}

    }

    my $service = $obj->{method} =~ /^system\./ if ( $obj );

    $self->status_line($result->status_line);

    if ($result->is_success) {

        return unless($result->content); # notification?

        if ($service) {
            return JSON::RPC::ServiceObject->new($result, $self->json);
        }

        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    elsif ($result->content_type eq 'application/json')
    {
        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    else {
        return;
    }
}


sub _post {
    my ($self, $uri, $headers, $obj) = @_;
    my $json = $self->json;

    $obj->{version} ||= $self->{version} || '1.1';

    if ($obj->{version} eq '1.0') {
        delete $obj->{version};
        if (exists $obj->{id}) {
            $self->id($obj->{id}) if ($obj->{id}); # if undef, it is notification.
        }
        else {
            $obj->{id} = $self->id || ($self->id('JSON::RPC::Client'));
        }
    }
    else {
        # $obj->{id} = $self->id if (defined $self->id);
	# Assign a random number to the id if one hasn't been set
	$obj->{id} = (defined $self->id) ? $self->id : substr(rand(),2);
    }

    my $content = $json->encode($obj);

    $self->ua->post(
        $uri,
        Content_Type   => $self->{content_type},
        Content        => $content,
        Accept         => 'application/json',
	@$headers,
	($self->{token} ? (Authorization => $self->{token}) : ()),
    );
}



1;
